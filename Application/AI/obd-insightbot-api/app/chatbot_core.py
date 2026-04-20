"""
OBD InsightBot - Chatbot Core Engine
=====================================
This module wraps the chatbot logic and provides async-compatible
interfaces for the FastAPI application.
"""

import asyncio
import json
import re
import random
import time
import logging
import gc
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from difflib import SequenceMatcher
from threading import Lock
import asyncio

logger = logging.getLogger(__name__)

# ====================
# DATA CLASSES
# ====================

@dataclass
class Intent:
    """Represents a user's intent with confidence score"""
    name: str
    confidence: float
    function_name: str
    arguments: Dict[str, Any]

    def to_json(self):
        return json.dumps({
            "name": self.function_name,
            "arguments": self.arguments
        })


# ====================
# DTC DATABASE
# ====================

DTC_DATABASE = {
    "P0300": {
        "description": "Random/Multiple Cylinder Misfire Detected",
        "severity": "HIGH",
        "possible_causes": [
            "Faulty spark plugs or ignition coils",
            "Vacuum leaks in the intake system",
            "Low fuel pressure or clogged injectors",
            "Worn engine components (pistons, valves)"
        ],
        "recommended_actions": [
            "Check and replace spark plugs if needed",
            "Inspect ignition coils for damage",
            "Test fuel pressure and check fuel filter",
            "Schedule a comprehensive diagnostic inspection"
        ],
        "estimated_cost": "£150-£500"
    },
    "P0171": {
        "description": "System Too Lean (Bank 1)",
        "severity": "MEDIUM",
        "possible_causes": [
            "Vacuum leak in intake manifold",
            "Faulty or dirty MAF sensor",
            "Weak fuel pump or clogged filter",
            "Exhaust leak near O2 sensor"
        ],
        "recommended_actions": [
            "Inspect all vacuum hoses for leaks",
            "Clean or replace MAF sensor",
            "Test fuel system pressure",
            "Check for exhaust leaks"
        ],
        "estimated_cost": "£100-£400"
    },
    "P0420": {
        "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "severity": "MEDIUM",
        "possible_causes": [
            "Failing catalytic converter",
            "Faulty oxygen sensors",
            "Engine running rich or lean",
            "Exhaust leaks"
        ],
        "recommended_actions": [
            "Test oxygen sensor readings",
            "Check for exhaust leaks",
            "Verify engine is running properly",
            "May need catalytic converter replacement"
        ],
        "estimated_cost": "£200-£1500"
    },
    "P0128": {
        "description": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
        "severity": "LOW",
        "possible_causes": [
            "Stuck-open thermostat",
            "Low coolant level",
            "Faulty coolant temperature sensor"
        ],
        "recommended_actions": [
            "Replace thermostat",
            "Check coolant level",
            "Test coolant temperature sensor"
        ],
        "estimated_cost": "£80-£200"
    }
}

SENSOR_RANGES = {
    "ENGINE_COOLANT_TEMP": {"min": 80, "max": 100, "unit": "°C"},
    "ENGINE_RPM": {"min": 600, "max": 3000, "unit": " RPM"},
    "FUEL_LEVEL": {"min": 25, "max": 100, "unit": "%"},
    "FUEL_PRESSURE": {"min": 30, "max": 60, "unit": " PSI"},
    "TYRE_PRESSURE": {"min": 30, "max": 35, "unit": " PSI"},
    "SPEED": {"min": 0, "max": 120, "unit": " km/h"},
    "THROTTLE_POS": {"min": 0, "max": 100, "unit": "%"},
    "ENGINE_LOAD": {"min": 0, "max": 100, "unit": "%"},
    "AMBIENT_AIR_TEMP": {"min": -10, "max": 40, "unit": "°C"},
    "AIR_INTAKE_TEMP": {"min": 0, "max": 60, "unit": "°C"},
    "INTAKE_MANIFOLD_PRESSURE": {"min": 20, "max": 100, "unit": " kPa"},
    "MAF": {"min": 2, "max": 25, "unit": " g/s"},
}

# Default vehicle data
DEFAULT_CAR_DATA = {
    "TIMESTAMP": 1502902504267,
    "MARK": "chevrolet",
    "MODEL": "agile",
    "CAR_YEAR": 2011,
    "ENGINE_POWER": 1.4,
    "AUTOMATIC": "n",
    "VEHICLE_ID": "car1",
    "BAROMETRIC_PRESSURE(KPA)": 100,
    "ENGINE_COOLANT_TEMP": 80,
    "FUEL_LEVEL": 48.60,
    "ENGINE_LOAD": 33.30,
    "AMBIENT_AIR_TEMP": 25,
    "ENGINE_RPM": 1009,
    "INTAKE_MANIFOLD_PRESSURE": 49,
    "MAF": 4.49,
    "FUEL_TYPE": "Biodiesel_Ethanol",
    "AIR_INTAKE_TEMP": 59,
    "FUEL_PRESSURE": 45,
    "SPEED": 0,
    "ENGINE_RUNTIME": "00:03:28",
    "THROTTLE_POS": 25,
    "DTC_NUMBER": "MIL is OFF 0 codes",
    "TROUBLE_CODES": ["P0300", "P0171"],
    "TIMING_ADVANCE": 56.9,
    "EQUIV_RATIO": 1.0,
    "TYRE_PRESSURE": 32
}


# ====================
# RESPONSE HUMANIZER
# ====================

class ResponseHumanizer:
    """Transforms technical responses into friendly, conversational language."""

    def __init__(self):
        self.greetings = [
            "Let me check that for you.",
            "Okay, let's see what's going on.",
            "Let me take a look.",
            "Checking that now.",
            "Let me see here."
        ]

        self.urgency_modifiers = {
            "HIGH": [
                "I'd get this looked at fairly soon.",
                "This one shouldn't wait too long.",
                "Worth prioritizing this one.",
                "I wouldn't put this off."
            ],
            "MEDIUM": [
                "Not urgent, but don't ignore it.",
                "You've got some time, but keep it on your radar.",
                "Schedule it when you can.",
                "Worth addressing in the next few weeks."
            ],
            "LOW": [
                "No rush on this one.",
                "Can wait until your next service.",
                "Minor issue, fix it when convenient.",
                "Low priority, but good to know about."
            ]
        }

        self.jargon_replacements = {
            "KPA": "pressure units",
            "PSI": "pressure",
            "RPM": "revs",
            "O2": "oxygen",
            "Bank 1": "one side of the engine",
            "Bank 2": "other side of the engine",
            "DTC": "error code",
            "MIL": "check engine light",
            "ECU": "car's computer",
            "PCM": "engine computer"
        }

        self.recent_phrases = []
        self.max_recent = 5

    def get_random_phrase(self, phrase_list: list) -> str:
        available = [p for p in phrase_list if p not in self.recent_phrases]
        if not available:
            available = phrase_list
            self.recent_phrases = []

        chosen = random.choice(available)
        if chosen:
            self.recent_phrases.append(chosen)
            if len(self.recent_phrases) > self.max_recent:
                self.recent_phrases.pop(0)
        return chosen

    def get_greeting(self) -> str:
        return self.get_random_phrase(self.greetings)

    def remove_jargon(self, text: str) -> str:
        result = text
        for jargon, replacement in self.jargon_replacements.items():
            result = re.sub(r'\b' + jargon + r'\b', replacement, result, flags=re.IGNORECASE)
        return result

    def humanize_code_explanation(self, code: str, dtc_database: dict, focus: str = "general") -> str:
        if code not in dtc_database:
            return f"I don't have specific information about code {code}."

        info = dtc_database[code]
        description = info['description']
        severity = info['severity']
        causes = info.get('possible_causes', [])
        cost = info.get('estimated_cost', 'Unknown')

        severity_text = {
            "HIGH": "This one shouldn't wait too long",
            "MEDIUM": "Less urgent, but good to address eventually",
            "LOW": "Not urgent, can wait until your next service"
        }

        response = f"So {code} means {description.lower()}. "

        if severity in severity_text:
            response += severity_text[severity] + ". "

        if causes and len(causes) > 0:
            response += f"Most commonly it's caused by {causes[0].lower()}. "

        response += f"Repair typically runs {cost}."

        return response

    def humanize_code_explanation_with_focus(self, code: str, dtc_database: dict, focus: str = "general") -> str:
        if code not in dtc_database:
            return f"Hmm, I don't have information about code {code} in my database."

        info = dtc_database[code]

        if focus == "actions":
            actions = info.get('recommended_actions', [])
            if actions:
                response = f"For {code}, here's what I recommend:\n"
                for i, action in enumerate(actions, 1):
                    action_text = action.replace("Check", "You'll want to check")
                    action_text = action_text.replace("Test", "Have someone test")
                    action_text = action_text.replace("Replace", "You might need to replace")
                    response += f"{i}. {action_text}\n"
                response += "\nI'd suggest starting with the simplest check first."
            else:
                response = f"I don't have specific repair steps for {code} right now."
            return response

        elif focus == "causes":
            causes = info.get('possible_causes', [])
            if causes:
                response = f"Code {code} typically happens because of:\n"
                for i, cause in enumerate(causes, 1):
                    cause_text = cause.lower()
                    response += f"{i}. {cause_text.capitalize()}\n"
                response += "\nThese are ordered from most to least common in my experience."
            else:
                response = f"I don't have cause information for {code} at the moment."
            return response

        elif focus == "cost":
            cost = info.get('estimated_cost', 'Unknown')
            severity = info.get('severity', 'Unknown')

            response = f"For {code} repairs, you're typically looking at {cost}. "

            if severity == "HIGH":
                response += "Since this is a high-priority issue, I'd budget for this soon."
            elif severity == "MEDIUM":
                response += "It's not super urgent, but don't put it off too long."
            elif severity == "LOW":
                response += "This isn't urgent, so you can plan for it at your next service."

            return response

        else:
            return self.humanize_code_explanation(code, dtc_database, focus="general")


# Global humanizer instance
humanizer = ResponseHumanizer()


# ====================
# RESPONSE CACHE
# ====================

class ResponseCache:
    """
    Simple in-memory cache for DTC code explanations and common queries.
    Reduces LLM calls and improves response time.
    TTL-based expiration to ensure fresh data.
    """

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 500):
        self.cache: Dict[str, tuple] = {}  # key -> (response, timestamp)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._lock = Lock()

    def _make_key(self, intent: str, params: Dict[str, Any]) -> str:
        """Create a cache key from intent and parameters."""
        # Sort params for consistent key generation
        sorted_params = sorted(params.items())
        params_str = "|".join(f"{k}={v}" for k, v in sorted_params)
        return f"{intent}:{params_str}"

    def get(self, intent: str, params: Dict[str, Any]) -> Optional[str]:
        """Get cached response if available and not expired."""
        key = self._make_key(intent, params)
        with self._lock:
            if key in self.cache:
                response, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    logger.debug(f"Cache hit for {intent}")
                    return response
                else:
                    # Expired, remove it
                    del self.cache[key]
        return None

    def set(self, intent: str, params: Dict[str, Any], response: str):
        """Store response in cache."""
        key = self._make_key(intent, params)
        with self._lock:
            # Evict oldest entries if cache is full
            if len(self.cache) >= self.max_entries:
                self._evict_oldest()
            self.cache[key] = (response, time.time())

    def _evict_oldest(self):
        """Remove oldest 10% of entries."""
        if not self.cache:
            return
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1][1])
        entries_to_remove = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:entries_to_remove]:
            del self.cache[key]

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self.cache.clear()


# Global response cache instance
response_cache = ResponseCache()


# ====================
# INTENT RECOGNIZER
# ====================

class IntentRecognizer:
    """Semantic-based intent recognition"""

    def __init__(self):
        self.dtc_pattern = re.compile(r'\b([PCBU][0-9]{4})\b', re.IGNORECASE)

        self.semantic_groups = {
            'status_health': [
                'status', 'doing', 'condition', 'health', 'check', 'okay', 'ok',
                'alright', 'fine', 'good', 'state', 'shape', 'running',
                'going', 'feeling', 'look', 'looking', 'seem', 'update', 'report',
                'summary', 'overview', 'diagnosis', 'diagnostic', 'well', 'up'
            ],
            'error_code': [
                'code', 'codes', 'error', 'errors', 'dtc',
                'diagnostic', 'warning', 'alert', 'light', 'lights'
            ],
            'engine': [
                'engine', 'motor', 'performance', 'power', 'rpm', 'idle',
                'running', 'start', 'starting'
            ],
            'fuel': [
                'fuel', 'gas', 'petrol', 'diesel', 'tank', 'range', 'mileage', 'much'
            ],
            'temperature': [
                'temperature', 'temp', 'hot', 'cold', 'heat', 'coolant',
                'overheating', 'warm', 'cooling'
            ],
            'vehicle_identity': [
                'what car', 'which car', 'what vehicle', 'what model',
                'car info', 'vehicle info', 'about my car', 'whats my car',
                'what year', 'which year', 'year is my car', 'my car year',
                'what is my car', 'tell me about my car', 'what am i driving',
                'what do i drive', 'my vehicle', 'vehicle year', 'car make',
                'car model', 'what make', 'what brand'
            ],
            'query_words': [
                'how', 'what', 'is', 'are', 'does', 'do', 'any', 'check',
                'can', 'could', 'tell', 'give', 'show', 'get', 'whats', 'hows'
            ],
            'car_references': [
                'car', 'vehicle', 'auto', 'automobile', 'it', 'my'
            ],
            'tyre': [
                'tyre', 'tire', 'tyres', 'tires', 'wheel', 'wheels'
            ],
        }

        # Symptom keywords that indicate diagnostic questions (should go to LLM)
        self.symptom_keywords = [
            'noise', 'noises', 'sound', 'sounds', 'weird', 'strange', 'odd',
            'vibration', 'vibrating', 'shaking', 'shake', 'wobble', 'wobbling',
            'smell', 'smells', 'smoke', 'smoking', 'leak', 'leaking', 'drip',
            'stall', 'stalling', 'dies', 'dying', 'rough', 'hesitate', 'hesitation',
            'grinding', 'squeaking', 'squealing', 'clicking', 'knocking', 'rattling',
            'pulling', 'drifting', 'hard to', 'difficult', 'wont', 'won\'t', 'doesnt', 'doesn\'t',
            'problem', 'problems', 'issue', 'issues', 'wrong', 'trouble', 'fault', 'faults'
        ]

        # Vehicle identity phrases - checked BEFORE status phrases
        self.vehicle_identity_phrases = [
            'what year', 'which year', 'what is my car', 'whats my car',
            'what car do i', 'what car am i', 'what am i driving',
            'what do i drive', 'tell me about my car', 'my car info',
            'car make', 'car model', 'what make', 'what brand', 'vehicle info',
            'about my car', 'car year', 'vehicle year', 'year of my car',
            'what kind of car', 'type of car', 'my vehicle info'
        ]

        # Common phrases for direct matching (more robust than word-level)
        self.status_phrases = [
            'how is my car', 'hows my car', 'how my car', 'car doing',
            'car status', 'check my car', 'my car okay', 'vehicle status',
            'whats up with my car', 'anything wrong', 'everything okay',
            'how s my car', 'what s up', 'is everything',
            'how are things', 'give me a status', 'quick check', 'checkup'
        ]

    def recognize(self, user_query: str, context: Dict[str, Any] = None) -> Optional[Intent]:
        query_lower = user_query.lower().strip()
        # Remove punctuation and normalize contractions for better matching
        query_clean = re.sub(r"[^\w\s]", " ", query_lower)  # Replace punctuation with space
        query_clean = re.sub(r"\s+", " ", query_clean).strip()  # Normalize whitespace
        query_words = set(query_clean.split())
        context = context or {}

        # Check for DTC code
        dtc_intent = self._check_dtc_code(user_query, query_lower)
        if dtc_intent:
            return dtc_intent

        # Check context follow-ups
        if context:
            context_intent = self._check_context_followup(query_lower, context)
            if context_intent:
                return context_intent

        # Check trigger phrases and semantic groups
        return self._check_semantic_groups(query_lower, query_words)

    def _check_dtc_code(self, query: str, query_lower: str) -> Optional[Intent]:
        dtc_match = re.search(r'[PBCU]\d{4}', query.upper())
        if dtc_match:
            code = dtc_match.group()
            arguments = {"code": code}

            if any(word in query_lower for word in ['cost', 'price', 'expensive', 'how much', 'much does it cost', 'gonna cost', 'will it cost']):
                arguments["focus"] = "cost"
            elif any(word in query_lower for word in ['action', 'recommend', 'what should', 'fix', 'repair', 'how to fix', 'how do i fix']):
                arguments["focus"] = "actions"
            elif any(word in query_lower for word in ['cause', 'why', 'reason', 'what causes']):
                arguments["focus"] = "causes"
            else:
                arguments["focus"] = "general"

            return Intent(
                name="explain_dtc_code",
                confidence=1.0,
                function_name="explain_dtc_code",
                arguments=arguments
            )
        return None

    def _check_context_followup(self, query_lower: str, context: Dict[str, Any]) -> Optional[Intent]:
        last_code = context.get('last_dtc_code')

        if last_code:
            cost_keywords = ['cost', 'price', 'expensive', 'how much']
            if any(k in query_lower for k in cost_keywords):
                return Intent("explain_dtc_cost", 0.9, "explain_dtc_code", {"code": last_code, "focus": "cost"})

            action_keywords = ['recommend', 'action', 'should i do', 'fix', 'repair']
            if any(k in query_lower for k in action_keywords):
                return Intent("explain_dtc_action", 0.9, "explain_dtc_code", {"code": last_code, "focus": "actions"})

            cause_keywords = ['cause', 'causes', 'why', 'reason']
            if any(k in query_lower for k in cause_keywords):
                return Intent("explain_dtc_cause", 0.9, "explain_dtc_code", {"code": last_code, "focus": "causes"})

        return None

    def _check_semantic_groups(self, query_lower: str, query_words: set) -> Optional[Intent]:
        # Check for symptom/diagnostic keywords FIRST - these should go to LLM
        if any(symptom in query_lower for symptom in self.symptom_keywords):
            return None  # Let LLM handle diagnostic questions

        # Check vehicle identity phrases BEFORE status phrases (more specific)
        if any(phrase in query_lower for phrase in self.vehicle_identity_phrases):
            return Intent("vehicle_info", 0.90, "get_vehicle_info", {})

        # Check common status phrases (most robust matching)
        if any(phrase in query_lower for phrase in self.status_phrases):
            return Intent("car_status", 0.90, "get_quick_summary", {})

        group_matches = {}
        for group_name, words in self.semantic_groups.items():
            matches = query_words.intersection(set(words))
            phrase_matches = sum(1 for phrase in words if ' ' in phrase and phrase in query_lower)
            group_matches[group_name] = len(matches) + phrase_matches

        # Greetings
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon']
        if any(g in query_lower for g in greetings) and len(query_words) <= 3:
            return Intent("greet", 0.95, "greet_user", {})

        # Vehicle identity
        if group_matches.get('vehicle_identity', 0) > 0:
            return Intent("vehicle_info", 0.85, "get_vehicle_info", {})

        # Error codes
        if group_matches.get('error_code', 0) > 0:
            return Intent("explain_all_codes", 0.85, "explain_all_active_codes", {})

        # Status/health queries
        has_status_words = group_matches.get('status_health', 0) > 0
        has_car_reference = group_matches.get('car_references', 0) > 0
        has_error_words = group_matches.get('error_code', 0) > 0

        # CHECK SPECIFIC SENSORS FIRST (before generic status)
        # This ensures "how is my tyre pressure" routes to tyre, not generic summary
        has_query_word = 'how' in query_words or 'what' in query_words or 'whats' in query_words or 'check' in query_words

        if has_query_word or has_car_reference:
            # Tyre/tire pressure - check first (most specific)
            if group_matches.get('tyre', 0) > 0 or any(t in query_lower for t in ['tyre', 'tire', 'tyres', 'tires']):
                return Intent("tyre_pressure", 0.90, "check_tyre_pressure", {})

            # Engine check
            if group_matches.get('engine', 0) > 0:
                return Intent("engine_status", 0.85, "get_engine_status", {})

            # Fuel check
            if group_matches.get('fuel', 0) > 0:
                return Intent("fuel_status", 0.85, "get_fuel_status", {})

            # Temperature check
            if group_matches.get('temperature', 0) > 0:
                return Intent("temperature_check", 0.80, "check_temperature_systems", {})

        # THEN check generic status (fallback for non-specific queries)
        if has_status_words and has_car_reference and not has_error_words:
            return Intent("car_status", 0.85, "get_quick_summary", {})

        if 'how' in query_words and has_car_reference and not has_error_words:
            return Intent("car_status", 0.80, "get_quick_summary", {})

        return None


# ====================
# DIALOG MANAGER
# ====================

class DialogManager:
    """Tracks conversation state for context-aware responses."""

    def __init__(self):
        self.entities_discussed = []
        self.pending_entities = []
        self.last_function = None
        self.last_args = {}
        self.last_dtc_code = None
        self.conversation_topic = None
        self.current_symptom = None  # Track symptom being discussed (e.g., "weird noise when starting")
        self.symptom_causes_suggested = []  # Track what causes we've already suggested
        self.message_history = []  # Store recent messages for LLM context

    def add_message(self, role: str, content: str):
        """Add a message to history, keeping last 10 messages."""
        self.message_history.append({"role": role, "content": content})
        if len(self.message_history) > 10:
            self.message_history.pop(0)

    def get_history_for_llm(self) -> str:
        """Format history for LLM prompt."""
        if not self.message_history:
            return ""
        history = "\n".join([f"{m['role']}: {m['content']}" for m in self.message_history[-6:]])
        return f"Recent conversation:\n{history}\n\n"

    def update_after_response(self, function_name: str, args: dict, car_data: dict):
        self.last_function = function_name
        self.last_args = args.copy() if args else {}

        if function_name == "explain_dtc_code":
            code = args.get("code", "").upper()
            if code:
                if code not in self.entities_discussed:
                    self.entities_discussed.append(code)
                self.last_dtc_code = code
                self.conversation_topic = "codes"

        elif function_name == "explain_all_active_codes":
            all_codes = car_data.get("TROUBLE_CODES", [])
            for code in all_codes:
                if code not in self.entities_discussed:
                    if code not in self.pending_entities:
                        self.pending_entities.append(code)
            self.conversation_topic = "codes"
            if all_codes and not self.last_dtc_code:
                self.last_dtc_code = all_codes[0]

        elif function_name == "get_quick_summary":
            self.conversation_topic = "status"

        elif function_name == "get_fuel_status":
            self.conversation_topic = "fuel"

        elif function_name == "get_engine_status":
            self.conversation_topic = "engine"

    def get_context(self) -> Dict[str, Any]:
        return {
            "last_function": self.last_function,
            "last_dtc_code": self.last_dtc_code,
            "conversation_topic": self.conversation_topic,
            "entities_discussed": self.entities_discussed,
            "pending_entities": self.pending_entities,
            "current_symptom": self.current_symptom,
            "symptom_causes_suggested": self.symptom_causes_suggested,
        }

    def set_symptom(self, symptom: str, suggested_cause: str = None):
        """Track a symptom discussion."""
        self.current_symptom = symptom
        self.conversation_topic = "symptoms"
        if suggested_cause:
            self.symptom_causes_suggested.append(suggested_cause)

    def reset(self):
        self.entities_discussed = []
        self.pending_entities = []
        self.last_function = None
        self.last_args = {}
        self.last_dtc_code = None
        self.conversation_topic = None
        self.current_symptom = None
        self.symptom_causes_suggested = []
        self.message_history = []


# ====================
# FUNCTION IMPLEMENTATIONS
# ====================

class FunctionExecutor:
    """Executes chatbot functions and generates responses."""

    def __init__(self, car_data: dict = None):
        self.car_data = car_data or DEFAULT_CAR_DATA.copy()

    def greet_user(self) -> str:
        return "Hi there! I'm InsightBot. I can help you check your car's status, explain error codes, or monitor sensors. What would you like to know?"

    def handle_off_topic(self) -> str:
        return "I'm designed to help with car diagnostics only. Is there anything about your vehicle I can help with?"

    def get_vehicle_info(self) -> str:
        make = self.car_data['MARK'].title()
        model = self.car_data['MODEL'].title()
        year = self.car_data['CAR_YEAR']
        engine = self.car_data['ENGINE_POWER']
        trans = "manual" if self.car_data['AUTOMATIC'] == 'n' else "automatic"
        fuel_type = self.car_data.get('FUEL_TYPE', 'Unknown').replace('_', '/')

        response = f"You're driving a {year} {make} {model}. "
        response += f"It's got a {engine}L {trans}."
        if fuel_type != "Unknown":
            response += f" Runs on {fuel_type.lower()}."

        return response

    def get_quick_summary(self) -> str:
        codes = self.car_data.get("TROUBLE_CODES", [])
        fuel = self.car_data.get("FUEL_LEVEL", 0)
        coolant = self.car_data.get("ENGINE_COOLANT_TEMP", 80)

        parts = [humanizer.get_greeting()]

        # Fuel status
        if fuel >= 50:
            parts.append(f"You've got plenty of fuel, about {int(fuel)}%.")
        elif fuel >= 25:
            parts.append(f"Fuel's at {int(fuel)}%, might want to top up soon.")
        else:
            parts.append(f"Heads up, fuel's getting low at {int(fuel)}%.")

        # Temperature
        if coolant < 70:
            parts.append("Engine's still warming up.")
        elif coolant <= 100:
            parts.append("Engine temp is good.")
        else:
            parts.append("Engine's running a bit hot, keep an eye on that.")

        # Codes
        if len(codes) == 0:
            parts.append("No error codes, which is great.")
        elif len(codes) == 1:
            parts.append("There's one error code showing up.")
        else:
            parts.append(f"There are {len(codes)} codes worth knowing about.")

        return " ".join(parts)

    def explain_dtc_code(self, code: str, focus: str = "general") -> str:
        code = code.upper().strip()

        if code not in DTC_DATABASE:
            available = ', '.join(DTC_DATABASE.keys())
            return f"Hmm, I don't have information about code {code}. Codes I know about: {available}"

        # Check cache first for DTC explanations
        cache_params = {"code": code, "focus": focus}
        cached_response = response_cache.get("explain_dtc_code", cache_params)
        if cached_response:
            return cached_response

        response = humanizer.humanize_code_explanation_with_focus(code, DTC_DATABASE, focus=focus)

        # Cache the response
        response_cache.set("explain_dtc_code", cache_params, response)

        return response

    def explain_all_active_codes(self) -> str:
        codes = self.car_data.get("TROUBLE_CODES", [])

        if not codes:
            return "Good news, no error codes showing up. Your car's running clean."

        parts = []

        if len(codes) == 1:
            parts.append("I found one code to tell you about.")
        else:
            parts.append(f"I found {len(codes)} codes. Let me walk you through them.")

        for code in codes:
            if code in DTC_DATABASE:
                info = DTC_DATABASE[code]
                desc = info.get('description', 'Unknown issue')
                severity = info.get('severity', 'MEDIUM')

                if severity == "HIGH":
                    parts.append(f"{code} means {desc.lower()}. This one shouldn't wait too long.")
                else:
                    parts.append(f"{code} is {desc.lower()}. Less urgent, but good to address eventually.")

        return " ".join(parts)

    def get_engine_status(self) -> str:
        rpm = self.car_data.get("ENGINE_RPM", 0)
        coolant = self.car_data.get("ENGINE_COOLANT_TEMP", 0)
        load = self.car_data.get("ENGINE_LOAD", 0)
        runtime = self.car_data.get("ENGINE_RUNTIME", "N/A")
        is_running = rpm > 400

        if not is_running:
            return "Your engine seems to be off right now. Start it up and ask me again for live readings."

        parts = [humanizer.get_greeting()]

        if rpm < 1000:
            parts.append(f"Engine's idling smoothly at {rpm} revs.")
        elif rpm < 2500:
            parts.append(f"Engine's running at {rpm} revs, nice and normal.")
        else:
            parts.append(f"Engine's running at {rpm} revs, that's on the higher side.")

        if coolant < 70:
            parts.append("Still warming up, give it a minute.")
        elif coolant <= 95:
            parts.append("Temperature's perfect.")
        elif coolant <= 105:
            parts.append("Running a little warm but okay.")
        else:
            parts.append("Running hot, I'd keep an eye on that gauge.")

        if load < 30:
            parts.append("Engine's basically relaxed right now.")
        elif load < 60:
            parts.append("Working at a comfortable level.")
        else:
            parts.append("Engine's working pretty hard at the moment.")

        if runtime and runtime != "N/A":
            parts.append(f"Been running for {runtime}.")

        return " ".join(parts)

    def get_fuel_status(self) -> str:
        fuel_level = self.car_data.get("FUEL_LEVEL", 0)
        fuel_pressure = self.car_data.get("FUEL_PRESSURE", 0)

        parts = []

        if fuel_level < 15:
            parts.append(f"You're running on fumes here, only {int(fuel_level)}% left. Time to find a station!")
        elif fuel_level < 25:
            parts.append(f"Getting low at {int(fuel_level)}%. I'd fill up soon if I were you.")
        elif fuel_level < 50:
            parts.append(f"About {int(fuel_level)}% in the tank, you've got some range left.")
        elif fuel_level < 75:
            parts.append(f"Sitting at {int(fuel_level)}%, plenty to work with.")
        else:
            parts.append(f"Tank's nice and full at {int(fuel_level)}%.")

        if fuel_pressure:
            if fuel_pressure < 30:
                parts.append(f"Fuel pressure is low though ({int(fuel_pressure)} PSI), might want to get the fuel pump checked.")
            elif fuel_pressure > 60:
                parts.append(f"Fuel pressure is a bit high ({int(fuel_pressure)} PSI), could be the pressure regulator.")

        return " ".join(parts)

    def check_temperature_systems(self) -> str:
        coolant = self.car_data.get("ENGINE_COOLANT_TEMP")
        ambient = self.car_data.get("AMBIENT_AIR_TEMP")
        intake = self.car_data.get("AIR_INTAKE_TEMP")

        parts = [humanizer.get_greeting()]

        if coolant is not None:
            if coolant < 70:
                parts.append(f"Engine coolant's at {coolant} degrees, still warming up.")
            elif coolant <= 100:
                parts.append(f"Engine coolant's at {coolant} degrees, right where you want it.")
            else:
                parts.append(f"Engine coolant's at {coolant} degrees, that's getting warm.")

        if ambient is not None:
            parts.append(f"It's {ambient} degrees outside.")

        if intake is not None:
            if intake > 50:
                parts.append(f"Intake air is {intake} degrees, a bit warm which can slightly affect performance.")
            else:
                parts.append(f"Intake air temp is good at {intake} degrees.")

        return " ".join(parts)

    def check_tyre_pressure(self) -> str:
        tyre_pressure = self.car_data.get("TYRE_PRESSURE", 0)
        parts = [humanizer.get_greeting()]

        if tyre_pressure == 0 or tyre_pressure is None:
            parts.append("I don't have tyre pressure data available for your vehicle.")
        elif tyre_pressure < 28:
            parts.append(f"Your tyre pressure is low at {tyre_pressure} PSI. You should inflate them soon.")
        elif tyre_pressure > 36:
            parts.append(f"Tyre pressure is a bit high at {tyre_pressure} PSI. Consider letting some air out.")
        else:
            parts.append(f"Tyre pressure looks good at {tyre_pressure} PSI, right in the normal range.")

        return " ".join(parts)


# ====================
# DYNAMIC OBD HANDLER
# ====================

class DynamicOBDHandler:
    """Handles dynamic OBD queries with natural language responses"""

    def __init__(self, car_data: dict, sensor_ranges: dict = None):
        self.car_data = car_data
        self.sensor_ranges = sensor_ranges or SENSOR_RANGES

        # Map natural language terms to OBD parameter names
        self.semantic_map = {
            'fuel': ['FUEL_LEVEL', 'FUEL_PRESSURE', 'FUEL_TYPE'],
            'temperature': ['ENGINE_COOLANT_TEMP', 'AMBIENT_AIR_TEMP', 'AIR_INTAKE_TEMP'],
            'coolant': ['ENGINE_COOLANT_TEMP'],
            'pressure': ['BAROMETRIC_PRESSURE', 'FUEL_PRESSURE', 'INTAKE_MANIFOLD_PRESSURE', 'TYRE_PRESSURE'],
            'engine': ['ENGINE_RPM', 'ENGINE_LOAD', 'ENGINE_RUNTIME', 'ENGINE_POWER'],
            'tire': ['TYRE_PRESSURE'],
            'tyre': ['TYRE_PRESSURE'],
            'speed': ['SPEED'],
            'throttle': ['THROTTLE_POS'],
            'air': ['AMBIENT_AIR_TEMP', 'AIR_INTAKE_TEMP', 'MAF'],
            'maf': ['MAF'],
            'rpm': ['ENGINE_RPM'],
            'load': ['ENGINE_LOAD'],
            'intake': ['INTAKE_MANIFOLD_PRESSURE', 'AIR_INTAKE_TEMP'],
            'battery': ['BATTERY_VOLTAGE'],
            'oil': ['OIL_TEMP', 'OIL_PRESSURE'],
        }

    def find_relevant_parameters(self, query: str) -> list:
        """Find OBD parameters relevant to the query"""
        query_lower = query.lower()
        relevant = []

        # Check for specific tire/tyre keywords first (more specific than generic "pressure")
        if 'tyre' in query_lower or 'tire' in query_lower:
            if 'TYRE_PRESSURE' in self.car_data:
                return ['TYRE_PRESSURE']

        for keyword, params in self.semantic_map.items():
            if keyword in query_lower:
                for param in params:
                    if param in self.car_data and param not in relevant:
                        relevant.append(param)

        return relevant

    def assess_value(self, param: str, value) -> dict:
        """Assess if a sensor value is normal, low, or high"""
        if param not in self.sensor_ranges:
            return {"status": "unknown", "value": value}

        ranges = self.sensor_ranges[param]
        min_val = ranges.get('min', float('-inf'))
        max_val = ranges.get('max', float('inf'))
        unit = ranges.get('unit', '')

        if value < min_val:
            return {"status": "low", "value": value, "unit": unit, "min": min_val, "max": max_val}
        elif value > max_val:
            return {"status": "high", "value": value, "unit": unit, "min": min_val, "max": max_val}
        else:
            return {"status": "normal", "value": value, "unit": unit, "min": min_val, "max": max_val}

    def generate_response(self, query: str) -> Optional[str]:
        """Generate a natural language response for the query"""
        relevant_params = self.find_relevant_parameters(query)

        if not relevant_params:
            return None  # Let other handlers deal with it

        responses = []
        for param in relevant_params:
            value = self.car_data.get(param)
            if value is None:
                continue

            assessment = self.assess_value(param, value)
            param_name = param.replace('_', ' ').title()

            if assessment["status"] == "normal":
                responses.append(f"{param_name} is at {value}{assessment.get('unit', '')}, which is normal.")
            elif assessment["status"] == "low":
                responses.append(f"{param_name} is at {value}{assessment.get('unit', '')}, which is a bit low (normal range: {assessment['min']}-{assessment['max']}{assessment.get('unit', '')}).")
            elif assessment["status"] == "high":
                responses.append(f"{param_name} is at {value}{assessment.get('unit', '')}, which is higher than normal (normal range: {assessment['min']}-{assessment['max']}{assessment.get('unit', '')}).")
            else:
                responses.append(f"{param_name} is currently at {value}.")

        if responses:
            return " ".join(responses)
        return None


# ====================
# SYMPTOM ADVISOR
# ====================

class SymptomAdvisor:
    """Provides rule-based diagnostic advice for common vehicle symptoms."""

    SYMPTOM_ADVICE = {
        'noise_accelerating': {
            'patterns': ['noise', 'sound', 'noises', 'sounds'],
            'conditions': ['accelerat', 'speed up', 'gas', 'throttle'],
            'advice': "Noises when accelerating often point to exhaust issues, worn engine mounts, or belt problems. Check under the hood for loose belts, and look underneath for exhaust hangers. If it's a whining sound, could be the transmission or power steering. Safe to drive short distances, but get it checked soon."
        },
        'noise_braking': {
            'patterns': ['noise', 'sound', 'squeal', 'squeak', 'grind'],
            'conditions': ['brak', 'stop', 'slow'],
            'advice': "Brake noises usually mean worn brake pads or warped rotors. Squealing often means pads are getting thin - a built-in warning. Grinding is more serious and means metal-on-metal contact. Get brakes inspected soon, especially if grinding."
        },
        'vibration_driving': {
            'patterns': ['vibrat', 'shak', 'wobbl'],
            'conditions': ['driv', 'highway', 'speed', 'fast'],
            'advice': "Vibration at speed often indicates unbalanced tires, worn suspension, or alignment issues. Check tire wear patterns - uneven wear suggests alignment problems. If it happens mainly when braking, could be warped rotors."
        },
        'vibration_idle': {
            'patterns': ['vibrat', 'shak', 'rough'],
            'conditions': ['idle', 'standstill', 'park', 'stop'],
            'advice': "Rough idle or vibration when stopped often points to spark plugs, ignition coils, or a vacuum leak. Also check engine mounts - worn mounts let vibration transfer to the cabin. Usually not urgent but should be diagnosed."
        },
        'smoke_exhaust': {
            'patterns': ['smoke', 'smoking'],
            'conditions': ['exhaust', 'tailpipe', 'back', 'behind'],
            'advice': "Blue smoke means burning oil (worn seals or rings). White smoke on a warm engine suggests coolant leak into combustion (head gasket). Black smoke means running too rich (too much fuel). White smoke when cold is usually just condensation and normal."
        },
        'smell_burning': {
            'patterns': ['smell', 'odor', 'odour'],
            'conditions': ['burn', 'hot'],
            'advice': "Burning smells need attention. Oil on hot exhaust smells acrid. Burning rubber could be a slipping belt or stuck brake. Sweet smell might be coolant leak. Check for fluid leaks under the car and look for smoke from the engine bay."
        },
        'stalling': {
            'patterns': ['stall', 'dies', 'cut out', 'shuts off'],
            'conditions': [],
            'advice': "Stalling can be fuel delivery (pump, filter, injectors), ignition (spark plugs, coils), or sensors (mass airflow, throttle position). If it happens when warm, often a sensor issue. When cold, often fuel-related. Check for any error codes."
        },
        'hard_start': {
            'patterns': ['hard to start', 'won\'t start', 'difficult start', 'slow start', 'cranks'],
            'conditions': [],
            'advice': "Hard starting when cold often points to a weak battery, worn spark plugs, or fuel system issues. When hot, could be a heat-soaked starter or vapor lock. Check battery terminals are clean and tight. If it cranks but won't fire, likely fuel or spark."
        },
        'pulling': {
            'patterns': ['pull', 'drift', 'veer'],
            'conditions': ['side', 'left', 'right', 'steer'],
            'advice': "Pulling to one side usually means alignment is off, uneven tire pressure, or a stuck brake caliper. Check tire pressures first - they should match side to side. If pressures are good, you likely need an alignment or brake inspection."
        },
        'leak': {
            'patterns': ['leak', 'drip', 'puddle', 'spot'],
            'conditions': [],
            'advice': "Fluid color helps identify leaks: Green/orange is coolant, brown/black is oil, red is transmission fluid, clear/light brown is brake fluid. Coolant and oil leaks are common but should be fixed. Brake fluid leaks are urgent - don't drive until fixed."
        }
    }

    @classmethod
    def get_advice(cls, message: str) -> Optional[str]:
        """Get diagnostic advice based on symptoms mentioned in the message."""
        message_lower = message.lower()

        for _, symptom_data in cls.SYMPTOM_ADVICE.items():
            # Check if any pattern matches
            pattern_match = any(p in message_lower for p in symptom_data['patterns'])
            if not pattern_match:
                continue

            # If there are conditions, at least one must match (or conditions list is empty)
            conditions = symptom_data['conditions']
            condition_match = not conditions or any(c in message_lower for c in conditions)

            if condition_match:
                return symptom_data['advice']

        return None


# ====================
# SESSION MANAGER
# ====================

class SessionManager:
    """Manages chat sessions with their own state."""

    # Session TTL in minutes - sessions older than this are cleaned up
    SESSION_TTL_MINUTES = 30
    # Cleanup interval in seconds
    CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes

    def __init__(self, max_sessions: int = 1000):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self._lock = Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    def create_session(self, session_id: str, custom_vehicle_data: Dict = None) -> Dict[str, Any]:
        with self._lock:
            # If session already exists, update it instead of creating new
            if session_id in self.sessions:
                if custom_vehicle_data:
                    # Update vehicle data for existing session
                    field_mapping = {
                        "mark": "MARK",
                        "model": "MODEL",
                        "car_year": "CAR_YEAR",
                        "engine_power": "ENGINE_POWER",
                        "automatic": "AUTOMATIC",
                        "fuel_type": "FUEL_TYPE",
                        "fuel_level": "FUEL_LEVEL",
                        "engine_coolant_temp": "ENGINE_COOLANT_TEMP",
                        "engine_rpm": "ENGINE_RPM",
                        "speed": "SPEED",
                        "trouble_codes": "TROUBLE_CODES",
                        "engine_runtime": "ENGINE_RUNTIME",
                        "engine_load": "ENGINE_LOAD",
                        "fuel_pressure": "FUEL_PRESSURE",
                        "ambient_air_temp": "AMBIENT_AIR_TEMP",
                        "air_intake_temp": "AIR_INTAKE_TEMP",
                        "throttle_pos": "THROTTLE_POS",
                    }
                    for key, value in custom_vehicle_data.items():
                        internal_key = field_mapping.get(key, key.upper())
                        if internal_key in self.sessions[session_id]["vehicle_data"]:
                            self.sessions[session_id]["vehicle_data"][internal_key] = value
                    self.sessions[session_id]["last_activity"] = datetime.utcnow().isoformat() + "Z"
                    logger.info(f"Updated existing session {session_id} with new vehicle data")
                return self.sessions[session_id]

            now = datetime.utcnow().isoformat() + "Z"

            # Build vehicle data
            vehicle_data = DEFAULT_CAR_DATA.copy()
            if custom_vehicle_data:
                logger.info(f"Received custom_vehicle_data: {custom_vehicle_data}")
                # Map custom data to internal format
                field_mapping = {
                    "mark": "MARK",
                    "model": "MODEL",
                    "car_year": "CAR_YEAR",
                    "engine_power": "ENGINE_POWER",
                    "automatic": "AUTOMATIC",
                    "fuel_type": "FUEL_TYPE",
                    "fuel_level": "FUEL_LEVEL",
                    "engine_coolant_temp": "ENGINE_COOLANT_TEMP",
                    "engine_rpm": "ENGINE_RPM",
                    "speed": "SPEED",
                    "trouble_codes": "TROUBLE_CODES",
                    "engine_runtime": "ENGINE_RUNTIME",
                    "engine_load": "ENGINE_LOAD",
                    "fuel_pressure": "FUEL_PRESSURE",
                    "ambient_air_temp": "AMBIENT_AIR_TEMP",
                    "air_intake_temp": "AIR_INTAKE_TEMP",
                    "throttle_pos": "THROTTLE_POS",
                }
                for key, value in custom_vehicle_data.items():
                    internal_key = field_mapping.get(key, key.upper())
                    if internal_key in vehicle_data:
                        logger.info(f"Setting {internal_key} = {value}")
                        vehicle_data[internal_key] = value
                    else:
                        logger.warning(f"Key {internal_key} not found in vehicle_data")

            session = {
                "created_at": now,
                "last_activity": now,
                "message_count": 0,
                "vehicle_data": vehicle_data,
                "dialog_manager": DialogManager(),
            }

            self.sessions[session_id] = session
            logger.info(f"Created new session {session_id} with custom vehicle data: {custom_vehicle_data is not None}")

            # Cleanup old sessions if needed
            if len(self.sessions) > self.max_sessions:
                self._cleanup_old_sessions()

            return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        return session

    def update_activity(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.utcnow().isoformat() + "Z"
            self.sessions[session_id]["message_count"] += 1

    def update_vehicle_data(self, session_id: str, updates: Dict) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False

        field_mapping = {
            "mark": "MARK",
            "model": "MODEL",
            "car_year": "CAR_YEAR",
            "engine_power": "ENGINE_POWER",
            "automatic": "AUTOMATIC",
            "fuel_type": "FUEL_TYPE",
            "fuel_level": "FUEL_LEVEL",
            "engine_coolant_temp": "ENGINE_COOLANT_TEMP",
            "engine_rpm": "ENGINE_RPM",
            "speed": "SPEED",
            "trouble_codes": "TROUBLE_CODES",
            "engine_runtime": "ENGINE_RUNTIME",
            "engine_load": "ENGINE_LOAD",
            "fuel_pressure": "FUEL_PRESSURE",
            "ambient_air_temp": "AMBIENT_AIR_TEMP",
            "air_intake_temp": "AIR_INTAKE_TEMP",
            "throttle_pos": "THROTTLE_POS",
        }

        for key, value in updates.items():
            internal_key = field_mapping.get(key, key.upper())
            if internal_key in session["vehicle_data"]:
                session["vehicle_data"][internal_key] = value

        return True

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def get_active_count(self) -> int:
        return len(self.sessions)

    def _cleanup_old_sessions(self):
        """Remove oldest sessions when max_sessions exceeded (overflow cleanup)."""
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1]["last_activity"]
        )
        sessions_to_remove = len(self.sessions) - self.max_sessions + 100
        for session_id, _ in sorted_sessions[:sessions_to_remove]:
            del self.sessions[session_id]
        logger.info(f"Overflow cleanup: removed {sessions_to_remove} sessions")

    def cleanup_expired_sessions(self) -> int:
        """
        Proactively cleanup sessions older than TTL.
        Returns the number of sessions removed.
        Critical for 4GB RAM constraint - prevents memory exhaustion.
        """
        with self._lock:
            cutoff = datetime.now(tz=None) - timedelta(minutes=self.SESSION_TTL_MINUTES)
            expired = []

            for session_id, session in self.sessions.items():
                try:
                    last_activity = session.get("last_activity", "")
                    # Handle both with and without 'Z' suffix
                    last_activity_str = last_activity.rstrip("Z")
                    last_time = datetime.fromisoformat(last_activity_str)
                    if last_time < cutoff:
                        expired.append(session_id)
                except (ValueError, TypeError):
                    # Invalid timestamp, mark for removal
                    expired.append(session_id)

            for session_id in expired:
                del self.sessions[session_id]

            if expired:
                logger.info(f"TTL cleanup: removed {len(expired)} expired sessions, {len(self.sessions)} remaining")
                # Force garbage collection after cleanup to free memory
                gc.collect()

            return len(expired)

    def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Started session cleanup background task")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped session cleanup background task")

    async def _periodic_cleanup(self):
        """Background task that periodically cleans up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL_SECONDS)
                removed = self.cleanup_expired_sessions()
                if removed > 0:
                    logger.debug(f"Periodic cleanup removed {removed} sessions")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")


# ====================
# CHATBOT ENGINE
# ====================

class ChatbotEngine:
    """Main engine that coordinates all chatbot components."""

    def __init__(self):
        self.is_ready = False
        self.session_manager = SessionManager()
        self.intent_recognizer = IntentRecognizer()
        self._start_time = None
        self._model = None
        self._model_lock = Lock()

    async def initialize(self):
        """Initialize the engine (load model if needed)."""
        logger.info("Initializing ChatbotEngine...")
        self._start_time = time.time()

        # Try to load the LLM model (optional - can work without it)
        try:
            await self._load_model()
        except Exception as e:
            logger.warning(f"Could not load LLM model: {e}. Using rule-based fallback.")

        # Start the session cleanup background task (critical for 4GB RAM)
        self.session_manager.start_cleanup_task()

        self.is_ready = True
        logger.info("ChatbotEngine initialized successfully")

    async def _load_model(self):
        """Load the Granite GGUF model."""
        try:
            from huggingface_hub import hf_hub_download
            from llama_cpp import Llama

            GGUF_REPO = "ibm-granite/granite-4.0-h-1b-GGUF"
            GGUF_FILENAME = "granite-4.0-h-1b-Q3_K_S.gguf"

            logger.info(f"Downloading model from {GGUF_REPO}...")
            gguf_path = hf_hub_download(
                repo_id=GGUF_REPO,
                filename=GGUF_FILENAME
            )

            logger.info("Loading model with llama.cpp...")
            self._model = Llama(
                model_path=gguf_path,
                n_ctx=1024,
                n_threads=4,
                verbose=False
            )
            logger.info("Model loaded successfully")
        except ImportError:
            logger.warning("llama-cpp-python not installed. Using rule-based processing only.")
            self._model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._model = None

    async def cleanup(self):
        """Cleanup resources."""
        # Stop the session cleanup task
        await self.session_manager.stop_cleanup_task()

        if self._model:
            del self._model
            self._model = None
        gc.collect()

    def get_uptime(self) -> float:
        if self._start_time:
            return time.time() - self._start_time
        return 0

    def get_dtc_database(self) -> Dict:
        return DTC_DATABASE

    def get_sensor_ranges(self) -> Dict:
        return SENSOR_RANGES

    async def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """Process a user message and generate a response."""

        # Get or create session
        session = self.session_manager.get_or_create_session(session_id)
        self.session_manager.update_activity(session_id)

        vehicle_data = session["vehicle_data"]
        dialog_manager = session["dialog_manager"]
        executor = FunctionExecutor(vehicle_data)

        # Get context for intent recognition
        context = dialog_manager.get_context()

        # Recognize intent
        intent = self.intent_recognizer.recognize(message, context)

        response = None
        detected_intent = None

        if intent:
            detected_intent = intent.function_name
            func_name = intent.function_name
            args = intent.arguments

            # Execute the function
            if func_name == "greet_user":
                response = executor.greet_user()
            elif func_name == "handle_off_topic":
                response = executor.handle_off_topic()
            elif func_name == "get_vehicle_info":
                response = executor.get_vehicle_info()
            elif func_name == "get_quick_summary":
                response = executor.get_quick_summary()
            elif func_name == "explain_dtc_code":
                response = executor.explain_dtc_code(
                    code=args.get("code", ""),
                    focus=args.get("focus", "general")
                )
            elif func_name == "explain_all_active_codes":
                response = executor.explain_all_active_codes()
            elif func_name == "get_engine_status":
                response = executor.get_engine_status()
            elif func_name == "get_fuel_status":
                response = executor.get_fuel_status()
            elif func_name == "check_temperature_systems":
                response = executor.check_temperature_systems()
            elif func_name == "check_tyre_pressure":
                response = executor.check_tyre_pressure()
            else:
                # Try to use LLM for unknown intents
                response = await self._try_llm_response(message, session)

            # Update dialog state
            if intent and response:
                dialog_manager.update_after_response(func_name, args, vehicle_data)

        if not response:
            # Check if this is a symptom/diagnostic question - skip DynamicOBD, go to LLM
            message_lower = message.lower()
            symptom_keywords = [
                'noise', 'noises', 'sound', 'sounds', 'weird', 'strange', 'odd',
                'vibration', 'vibrating', 'shaking', 'shake', 'wobble', 'wobbling',
                'smell', 'smells', 'smoke', 'smoking', 'leak', 'leaking', 'drip',
                'stall', 'stalling', 'dies', 'dying', 'rough', 'hesitate', 'hesitation',
                'grinding', 'squeaking', 'squealing', 'clicking', 'knocking', 'rattling',
                'pulling', 'drifting', 'hard to', 'difficult', 'problem', 'issue', 'wrong'
            ]
            is_symptom_query = any(kw in message_lower for kw in symptom_keywords)

            # Check if this is a follow-up to a symptom discussion
            followup_keywords = ['what else', 'else could', 'other cause', 'another', 'besides', 'still', 'already checked', 'is good', 'is fine', 'ruled out']
            is_symptom_followup = any(kw in message_lower for kw in followup_keywords) and dialog_manager.conversation_topic == "symptoms"

            if is_symptom_query:
                # Set symptom context for the LLM
                dialog_manager.set_symptom(message)
            elif is_symptom_followup:
                # This is a follow-up, keep the symptom context
                pass

            if not is_symptom_query and not is_symptom_followup:
                # Try DynamicOBDHandler for sensor-related queries
                dynamic_handler = DynamicOBDHandler(vehicle_data, SENSOR_RANGES)
                response = dynamic_handler.generate_response(message)
                if response:
                    detected_intent = "dynamic_obd_query"

        if not response:
            # For symptom questions, try rule-based SymptomAdvisor first (more reliable)
            message_lower = message.lower()
            is_symptom = any(kw in message_lower for kw in [
                'noise', 'sound', 'vibrat', 'shak', 'smell', 'smoke', 'leak',
                'stall', 'dies', 'pull', 'drift', 'grind', 'squeal', 'click', 'knock', 'rattle'
            ])

            if is_symptom:
                symptom_advice = SymptomAdvisor.get_advice(message)
                if symptom_advice:
                    response = symptom_advice
                    detected_intent = "symptom_advisor"

        if not response:
            # Try LLM fallback for diagnostic/symptom questions and general queries
            response = await self._try_llm_response(message, session)
            if response:
                detected_intent = "llm_fallback"
                # If LLM responded about a symptom, try to extract what cause it suggested
                if dialog_manager.conversation_topic == "symptoms" and dialog_manager.current_symptom:
                    # Track suggested causes from response for follow-up questions
                    cause_indicators = ['check the', 'could be', 'might be', 'probably', 'likely']
                    for indicator in cause_indicators:
                        if indicator in response.lower():
                            # Extract a simple cause description from response
                            dialog_manager.symptom_causes_suggested.append(response[:50])

        if not response:
            # Final fallback response
            response = "I'm not sure how to help with that. Try asking about your car status, error codes, or fuel level."
            detected_intent = "unknown"

        # Remove jargon from response
        response = humanizer.remove_jargon(response)

        # Store messages in history for conversation context
        dialog_manager.add_message("User", message)
        dialog_manager.add_message("Assistant", response)

        return {
            "response": response,
            "intent": detected_intent
        }

    async def _try_llm_response(self, message: str, session: Dict) -> Optional[str]:
        """Try to generate a response using the LLM model."""
        if not self._model:
            return None

        try:
            vehicle_data = session.get("vehicle_data", {})
            dialog_manager = session.get("dialog_manager")
            car_info = f"{vehicle_data.get('CAR_YEAR', '')} {vehicle_data.get('MARK', '').title()} {vehicle_data.get('MODEL', '').title()}".strip()

            # Build vehicle context with sensor data
            trouble_codes = vehicle_data.get('TROUBLE_CODES', [])
            codes_str = ', '.join(trouble_codes) if trouble_codes else 'None'
            fuel_level = vehicle_data.get('FUEL_LEVEL', 'Unknown')
            coolant_temp = vehicle_data.get('ENGINE_COOLANT_TEMP', 'Unknown')
            rpm = vehicle_data.get('ENGINE_RPM', 'Unknown')

            # Get conversation history for context
            history = ""
            symptom_context = ""
            if dialog_manager:
                history = dialog_manager.get_history_for_llm()
                # Add symptom context if we're in a diagnostic conversation
                context = dialog_manager.get_context()
                if context.get("current_symptom"):
                    symptom_context = f"Current symptom: {context['current_symptom']}\n"
                    if context.get("symptom_causes_suggested"):
                        symptom_context += f"Already suggested: {', '.join(context['symptom_causes_suggested'][:3])}\n"

            # Detect if this is a symptom-based question
            message_lower = message.lower()
            is_symptom_question = any(kw in message_lower for kw in [
                'noise', 'sound', 'weird', 'strange', 'vibration', 'shaking',
                'smell', 'smoke', 'leak', 'stall', 'rough', 'grinding', 'squeaking',
                'clicking', 'knocking', 'rattling', 'pulling', 'problem', 'issue', 'wrong'
            ])

            # Build symptom-specific guidance if applicable
            symptom_guidance = ""
            if is_symptom_question or symptom_context:
                symptom_guidance = """
IMPORTANT - For symptom questions:
- Suggest 2-3 possible causes based on the symptom described
- Mention what the user can check themselves (visual inspection, listen for patterns)
- Indicate if it's safe to keep driving or needs immediate attention
- DO NOT just repeat vehicle stats - give actual diagnostic advice
"""

            # Improved system prompt with clear guidelines
            prompt = f"""You are InsightBot, a friendly automotive diagnostic assistant. Give helpful, concise advice.

GUIDELINES:
- Use simple everyday language, avoid technical jargon
- Suggest simple checks before expensive repairs
- Be honest about severity - don't alarm unnecessarily
- Keep responses to 2-3 sentences maximum
- If unsure, recommend consulting a mechanic
{symptom_guidance}
VEHICLE INFO:
- Car: {car_info if car_info else 'Unknown vehicle'}
- Active codes: {codes_str}
- Fuel: {fuel_level}% | Coolant: {coolant_temp}C | RPM: {rpm}

{symptom_context}{history}User: {message}

InsightBot:"""

            with self._model_lock:
                result = self._model(
                    prompt,
                    max_tokens=150,  # Reduced for more concise responses
                    temperature=0.6,  # Slightly lower for more focused responses
                    top_p=0.85,
                    stop=["User:", "\n\n", "GUIDELINES:", "VEHICLE INFO:"]
                )

            response = result["choices"][0]["text"].strip()
            # Clean up any artifacts
            response = response.strip('"').strip()
            # Remove leading colons, "InsightBot:", newlines
            response = re.sub(r'^[:\s]*(?:InsightBot:)?\s*', '', response)
            # Limit response to first 3 sentences to avoid repetition
            sentences = re.split(r'(?<=[.!?])\s+', response)
            if len(sentences) > 3:
                response = ' '.join(sentences[:3])
            # Return if we got a meaningful response
            if response and len(response) > 10:
                return response
            logger.warning(f"LLM response too short: '{response}'")
            return None
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None


# Singleton getter
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
