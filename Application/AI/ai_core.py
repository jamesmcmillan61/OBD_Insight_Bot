from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import json
import re
from datetime import datetime
import random
from difflib import SequenceMatcher
from typing import Optional, Dict, Any
from dataclasses import dataclass

import os
import psutil

def print_memory_usage(note=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # MB
    print(f"[Memory] {note}: {mem:.1f} MB")

# Download a GGUF quantized Granite model file from Hugging Face
# Repo: ibm-granite/granite-4.0-h-1b-GGUF

GGUF_REPO = "ibm-granite/granite-4.0-h-1b-GGUF"

# Pick a quant file. Start with Q4_K_M (good balance).
# The exact filename must match one that exists in the repo.
GGUF_FILENAME = "granite-4.0-h-1b-Q4_K_M.gguf"

gguf_path = hf_hub_download(
    repo_id=GGUF_REPO,
    filename=GGUF_FILENAME
)

print_memory_usage("before loading model")

# Load model with llama.cpp
llm = Llama(
    model_path=gguf_path,
    n_ctx=1024,      # keep small (512-1024) to save RAM
    n_threads=4,     # set this to your VM CPU cores (or leave 4)
    verbose=False
)

print("Loaded Granite GGUF with llama.cpp:", gguf_path)
print_memory_usage("after loading model")

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
    },
    "P0001": {
    "description": "Fuel Volume Regulator Control Circuit/Open",
    "severity": "High",
    "possible_causes": [
      "Faulty fuel volume regulator",
      "Open wiring in fuel regulator circuit",
      "Short circuit in wiring",
      "ECU malfunction"
    ],
    "recommended_actions": [
      "Inspect wiring and connectors",
      "Test fuel volume regulator",
      "Check ECU signals with diagnostic scanner",
      "Replace faulty regulator if needed"
    ],
    "estimated_cost": "£80–£400"
  },

  "P0100": {
    "description": "Mass or Volume Air Flow Circuit Malfunction",
    "severity": "Medium",
    "possible_causes": [
      "Dirty or faulty MAF sensor",
      "Air intake leak",
      "Damaged wiring to MAF sensor",
      "Faulty ECU"
    ],
    "recommended_actions": [
      "Clean the MAF sensor",
      "Check intake hoses for leaks",
      "Inspect wiring and connectors",
      "Replace MAF sensor if faulty"
    ],
    "estimated_cost": "£60–£250"
  },
  "P0101": {
    "description": "Mass Air Flow (MAF) Circuit Range/Performance Problem",
    "severity": "Medium",
    "possible_causes": [
      "Dirty or faulty MAF sensor",
      "Air intake restriction",
      "Vacuum leak",
      "Damaged wiring to MAF sensor"
    ],
    "recommended_actions": [
      "Clean or replace the MAF sensor",
      "Inspect air intake system",
      "Check for vacuum leaks",
      "Inspect wiring and connectors"
    ],
    "estimated_cost": "£70–£250"
  },

  "P0110": {
    "description": "Intake Air Temperature Sensor Circuit Malfunction",
    "severity": "Low",
    "possible_causes": [
      "Faulty intake air temperature sensor",
      "Open or short circuit wiring",
      "Corroded connector",
      "ECU issue"
    ],
    "recommended_actions": [
      "Test intake air temperature sensor",
      "Inspect wiring and connectors",
      "Replace faulty sensor",
      "Clear codes and retest"
    ],
    "estimated_cost": "£40–£150"
  },

  "P0120": {
    "description": "Throttle Position Sensor/Switch A Circuit Malfunction",
    "severity": "High",
    "possible_causes": [
      "Faulty throttle position sensor",
      "Damaged wiring",
      "Throttle body issues",
      "ECU fault"
    ],
    "recommended_actions": [
      "Test throttle position sensor",
      "Inspect throttle body",
      "Check wiring and connectors",
      "Replace sensor if necessary"
    ],
    "estimated_cost": "£80–£300"
  },

  "P0130": {
    "description": "Oxygen Sensor Circuit Malfunction (Bank 1 Sensor 1)",
    "severity": "Medium",
    "possible_causes": [
      "Faulty oxygen sensor",
      "Exhaust leak",
      "Wiring damage",
      "ECU malfunction"
    ],
    "recommended_actions": [
      "Test oxygen sensor voltage",
      "Inspect exhaust system for leaks",
      "Check wiring and connectors",
      "Replace oxygen sensor if faulty"
    ],
    "estimated_cost": "£90–£220"
  },

  "P0201": {
    "description": "Injector Circuit Malfunction Cylinder 1",
    "severity": "High",
    "possible_causes": [
      "Faulty fuel injector",
      "Open or short in injector wiring",
      "ECU driver issue",
      "Connector corrosion"
    ],
    "recommended_actions": [
      "Test fuel injector resistance",
      "Inspect wiring harness",
      "Clean or replace injector",
      "Check ECU signal"
    ],
    "estimated_cost": "£120–£350"
  },

  "P0301": {
    "description": "Cylinder 1 Misfire Detected",
    "severity": "High",
    "possible_causes": [
      "Faulty spark plug",
      "Bad ignition coil",
      "Fuel injector malfunction",
      "Low compression"
    ],
    "recommended_actions": [
      "Replace spark plug",
      "Test ignition coil",
      "Inspect injector operation",
      "Perform compression test"
    ],
    "estimated_cost": "£80–£500"
  },

  "P0401": {
    "description": "Exhaust Gas Recirculation Flow Insufficient Detected",
    "severity": "Medium",
    "possible_causes": [
      "Blocked EGR valve",
      "Faulty EGR valve",
      "Carbon buildup in EGR passages",
      "Vacuum line issues"
    ],
    "recommended_actions": [
      "Clean EGR valve",
      "Inspect vacuum lines",
      "Check EGR passages",
      "Replace EGR valve if needed"
    ],
    "estimated_cost": "£120–£400"
  },

  "P0442": {
    "description": "Evaporative Emission Control System Leak Detected (Small Leak)",
    "severity": "Low",
    "possible_causes": [
      "Loose gas cap",
      "Cracked EVAP hose",
      "Faulty purge valve",
      "Damaged charcoal canister"
    ],
    "recommended_actions": [
      "Tighten or replace gas cap",
      "Inspect EVAP hoses",
      "Test purge valve",
      "Repair leaks in EVAP system"
    ],
    "estimated_cost": "£30–£200"
  },

  "P0500": {
    "description": "Vehicle Speed Sensor Malfunction",
    "severity": "Medium",
    "possible_causes": [
      "Faulty vehicle speed sensor",
      "Damaged wiring",
      "ABS sensor issue",
      "ECU fault"
    ],
    "recommended_actions": [
      "Test vehicle speed sensor",
      "Inspect wiring and connectors",
      "Check ABS sensor signals",
      "Replace faulty sensor"
    ],
    "estimated_cost": "£70–£250"
  },

}

SENSOR_RANGES = {
    "ENGINE_COOLANT_TEMP": {"min": 80, "max": 100, "unit": "°C"},
    "ENGINE_RPM": {"min": 600, "max": 3000, "unit": "RPM"},
    "FUEL_LEVEL": {"min": 25, "max": 100, "unit": "%"},
    "FUEL_PRESSURE": {"min": 30, "max": 60, "unit": "PSI"},
    "TYRE_PRESSURE": {"min": 70, "max": 100, "unit": "PSI"},
    "SPEED": {"min": 0, "max": 120, "unit": "km/h"},
    "THROTTLE_POS": {"min": 0, "max": 100, "unit": "%"},
    "ENGINE_LOAD": {"min": 0, "max": 100, "unit": "%"}
}

class ResponseHumanizer:
    """
    Transforms technical responses into friendly, conversational language.
    Makes the bot sound like a helpful friend rather than a computer.
    """

    def __init__(self):
        # Technical term to everyday analogy mappings
        self.analogies = {
            "misfire": [
                "stuttering", "hiccupping", "skipping beats",
                "running rough", "stumbling"
            ],
            "lean condition": [
                "not getting enough fuel", "running on too much air",
                "like trying to run on an empty stomach", "fuel-starved"
            ],
            "rich condition": [
                "getting too much fuel", "drowning in fuel",
                "like overeating", "fuel-flooded"
            ],
            "catalytic converter": [
                "exhaust cleaner", "emissions filter",
                "the part that cleans your exhaust"
            ],
            "oxygen sensor": [
                "O2 sensor", "exhaust monitor",
                "the sensor that checks your exhaust"
            ],
            "MAF sensor": [
                "airflow sensor", "air measuring sensor",
                "the part that measures how much air goes in"
            ],
            "thermostat": [
                "temperature regulator", "cooling system valve",
                "what controls your engine temperature"
            ],
            "spark plugs": [
                "ignition sparkers", "the parts that ignite the fuel",
                "what makes the engine fire"
            ]
        }

        # Jargon replacements for cleaner output
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

        # Tone variations for different situations
        self.greetings = [
            "Let me check that for you.",
            "Okay, let's see what's going on.",
            "Let me take a look.",
            "Checking that now.",
            "Let me see here."
        ]

        self.good_news_starters = [
            "Good news",
            "Looking good",
            "All clear on that",
            "Nothing to worry about there"
        ]

        self.concern_starters = [
            "I found something worth mentioning",
            "There's something that needs attention",
            "Your car's telling me about an issue",
            "I noticed something here"
        ]

        self.explanation_starters = [
            "Here's what's happening",
            "Let me explain",
            "What this means is",
            "Basically",
            "In simple terms"
        ]

        self.reassurance_phrases = [
            "This is actually pretty common.",
            "I see this fairly often.",
            "Don't worry, this is usually straightforward to fix.",
            "This is a known issue with a clear solution.",
            "The good news is this is typically fixable."
        ]

        self.cost_empathy = [
            "I know repairs can add up, but",
            "The cost might seem high, but it's worth addressing",
            "It's an investment in keeping your car healthy"
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

        self.closing_phrases = [
            "Let me know if you have questions.",
            "Happy to explain more if needed.",
            "Anything else you'd like to know?",
            ""  # Sometimes no closing is natural
        ]

        # Track recent phrases to avoid repetition
        self.recent_phrases = []
        self.max_recent = 5

    def get_random_phrase(self, phrase_list: list) -> str:
        """Get a random phrase, avoiding recent repetitions"""
        available = [p for p in phrase_list if p not in self.recent_phrases]
        if not available:
            available = phrase_list
            self.recent_phrases = []

        chosen = random.choice(available)
        if chosen:  # Don't track empty strings
            self.recent_phrases.append(chosen)
            if len(self.recent_phrases) > self.max_recent:
                self.recent_phrases.pop(0)
        return chosen

    def get_greeting(self) -> str:
        """Get a varied greeting"""
        return self.get_random_phrase(self.greetings)

    def get_closing(self) -> str:
        """Get a varied closing phrase"""
        return self.get_random_phrase(self.closing_phrases)

    def get_analogy(self, technical_term: str) -> str:
        """Get a human-friendly analogy for a technical term"""
        term_lower = technical_term.lower()
        for key, analogies in self.analogies.items():
            if key in term_lower:
                return random.choice(analogies)
        return technical_term

    def remove_jargon(self, text: str) -> str:
        """Replace technical jargon with friendlier terms"""
        result = text
        for jargon, replacement in self.jargon_replacements.items():
            result = re.sub(r'\b' + jargon + r'\b', replacement, result, flags=re.IGNORECASE)
        return result

    def get_severity_comment(self, severity: str) -> str:
        """Get an appropriate urgency comment based on severity"""
        urgency_list = self.urgency_modifiers.get(severity.upper(), self.urgency_modifiers["MEDIUM"])
        return self.get_random_phrase(urgency_list)

    def get_reassurance(self) -> str:
        """Get a reassuring phrase"""
        return self.get_random_phrase(self.reassurance_phrases)

    def humanize_number(self, value: float, context: str = "") -> str:
        """Make numbers more conversational"""
        if context == "percentage":
            if value >= 75:
                return f"about {int(value)}%, nice and full"
            elif value >= 50:
                return f"around {int(value)}%, about half"
            elif value >= 25:
                return f"about {int(value)}%, getting lower"
            else:
                return f"only {int(value)}%, pretty low"
        elif context == "temperature":
            return f"{int(value)} degrees"
        elif context == "currency":
            return f"around {value}"
        return str(value)

    def build_progressive_response(self, simple: str, detail: str = None, technical: str = None) -> str:
        """Build a response with progressive disclosure"""
        response = simple
        if detail:
            response += f" {detail}"
        # Technical details can be added if user asks for more
        return response

    def humanize_code_explanation(self, code, dtc_database, focus="general"):
      """Generate natural explanation for a single DTC code"""
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

    def humanize_code_explanation_with_focus(self, code, dtc_database, focus="general"):
      """Generate natural explanation for a DTC code with optional focus"""
      if code not in dtc_database:
          return f"Hmm, I don't have information about code {code} in my database."

      info = dtc_database[code]

      # Handle different focus types
      if focus == "actions":
          actions = info.get('recommended_actions', [])
          if actions:
              response = f"For {code}, here's what I recommend:\n"
              for i, action in enumerate(actions, 1):
                  # Make actions conversational
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
                  # Make causes more conversational
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
          # For general focus, call the existing method with correct parameters
          # Fix: Pass only the required 3 parameters (self, code, dtc_database)
          return self.humanize_code_explanation(code, dtc_database, focus="general")

    def _explain_actions(self, code: str, info: dict) -> str:
        """Generate focused response about recommended actions"""
        actions = info.get('recommended_actions', [])

        if not actions:
            return f"I don't have specific action recommendations for {code}, but generally I'd suggest having a mechanic run a diagnostic."

        intros = [
            f"For {code}, here's what I'd recommend doing:",
            f"To address {code}, these are the steps I'd suggest:",
            f"Here's how I'd tackle {code}:"
        ]

        response = self.get_random_phrase(intros) + " "

        if len(actions) == 1:
            response += f"The main thing is to {actions[0].lower()}."
        else:
            response += f"First, {actions[0].lower()}. "
            for i, action in enumerate(actions[1:], 2):
                if i == len(actions):
                    response += f"Finally, {action.lower()}."
                else:
                    response += f"Then, {action.lower()}. "

        tips = [
            "Start with the simplest fix first, it's often the cheapest.",
            "Work through these in order, sometimes the first fix solves everything.",
            "A good mechanic can help narrow down which step you actually need."
        ]
        response += " " + self.get_random_phrase(tips)

        return response

    def _explain_causes(self, code: str, info: dict) -> str:
        """Generate focused response about possible causes"""
        causes = info.get('possible_causes', [])

        if not causes:
            return f"I don't have specific cause information for {code}. A diagnostic scan would help identify the root cause."

        intros = [
            f"Code {code} is typically caused by:",
            f"There are a few things that can trigger {code}:",
            f"Here's what usually causes {code}:"
        ]

        response = self.get_random_phrase(intros) + " "

        if len(causes) == 1:
            response += f"Most commonly, it's {causes[0].lower()}."
        else:
            response += f"Most often, it's {causes[0].lower()}. "
            if len(causes) == 2:
                response += f"It could also be {causes[1].lower()}."
            else:
                response += f"Other possibilities include {causes[1].lower()}"
                for cause in causes[2:]:
                    response += f", or {cause.lower()}"
                response += "."

        response += " These are listed roughly from most to least common."

        return response

    def _explain_cost(self, code: str, info: dict) -> str:
        """Generate focused response about repair costs"""
        cost = info.get('estimated_cost', None)
        severity = info.get('severity', 'MEDIUM')

        if not cost:
            return f"I don't have specific cost estimates for {code}. Prices vary a lot depending on your location and the actual cause."

        intros = [
            f"For {code} repairs, you're typically looking at",
            f"Fixing {code} usually costs",
            f"Budget-wise, {code} repairs generally run"
        ]

        response = f"{self.get_random_phrase(intros)} {cost}. "

        if severity == "HIGH":
            response += "Since this is a high-priority issue, I'd budget for this sooner rather than later. "
            response += "Putting it off could lead to more expensive problems."
        elif severity == "MEDIUM":
            response += "It's not super urgent, but don't put it off too long. "
            response += "You can shop around for quotes."
        else:
            response += "This isn't urgent, so you can plan for it at your convenience. "
            response += "Maybe bundle it with your next service to save on labor."

        tips = [
            "Prices can vary quite a bit between shops, so it's worth getting a couple quotes.",
            "Independent mechanics are often cheaper than dealerships for this kind of work.",
            "The actual cost depends on what's causing the code, so diagnosis comes first."
        ]
        response += " " + self.get_random_phrase(tips)

        return response

    def humanize_status(self, fuel: float, temp: float, temp_status: str,
                        code_count: int, has_high_priority: bool) -> str:
        """Create a human-friendly status summary"""
        parts = []

        # Greeting
        parts.append(self.get_greeting())

        # Fuel status - conversational
        if fuel >= 50:
            parts.append(f"You've got plenty of fuel, about {int(fuel)}%.")
        elif fuel >= 25:
            parts.append(f"Fuel's at {int(fuel)}%, might want to top up soon.")
        else:
            parts.append(f"Heads up, fuel's getting low at {int(fuel)}%.")

        # Temperature - simple
        if temp_status == "normal":
            parts.append("Engine temp is good.")
        elif temp_status == "cold":
            parts.append("Engine's still warming up.")
        else:
            parts.append("Engine's running a bit hot, keep an eye on that.")

        # Codes - with appropriate concern
        if code_count == 0:
            parts.append("No error codes, which is great.")
        elif code_count == 1:
            if has_high_priority:
                parts.append("There's one error code that needs attention.")
            else:
                parts.append("There's one minor code showing up.")
        else:
            if has_high_priority:
                parts.append(f"There are {code_count} codes, and at least one is important to address.")
            else:
                parts.append(f"There are {code_count} codes, nothing urgent but worth knowing about.")

        return " ".join(parts)

    def humanize_engine_status(self, rpm: int, coolant: float, load: float,
                                runtime: str, is_running: bool) -> str:
        """Create a human-friendly engine status"""
        if not is_running:
            return "Your engine seems to be off right now. Start it up and ask me again for live readings."

        parts = [self.get_greeting()]

        # RPM - simple context
        if rpm < 1000:
            parts.append(f"Engine's idling smoothly at {rpm} revs.")
        elif rpm < 2500:
            parts.append(f"Engine's running at {rpm} revs, nice and normal.")
        else:
            parts.append(f"Engine's running at {rpm} revs, that's on the higher side.")

        # Temperature - relatable
        if coolant < 70:
            parts.append("Still warming up, give it a minute.")
        elif coolant <= 95:
            parts.append("Temperature's perfect.")
        elif coolant <= 105:
            parts.append("Running a little warm but okay.")
        else:
            parts.append("Running hot, I'd keep an eye on that gauge.")

        # Load - simple
        if load < 30:
            parts.append("Engine's basically relaxed right now.")
        elif load < 60:
            parts.append("Working at a comfortable level.")
        else:
            parts.append("Engine's working pretty hard at the moment.")

        if runtime and runtime != "N/A":
            parts.append(f"Been running for {runtime}.")

        return " ".join(parts)

    def humanize_fuel_status(self, level: float, pressure: float) -> str:
        """Create a human-friendly fuel status"""
        parts = []

        # Level with personality
        if level < 15:
            parts.append(f"You're running on fumes here, only {int(level)}% left. Time to find a station!")
        elif level < 25:
            parts.append(f"Getting low at {int(level)}%. I'd fill up soon if I were you.")
        elif level < 50:
            parts.append(f"About {int(level)}% in the tank, you've got some range left.")
        elif level < 75:
            parts.append(f"Sitting at {int(level)}%, plenty to work with.")
        else:
            parts.append(f"Tank's nice and full at {int(level)}%.")

        # Pressure - only mention if abnormal
        if pressure:
            if pressure < 30:
                parts.append(f"Fuel pressure is low though ({int(pressure)} PSI), might want to get the fuel pump checked.")
            elif pressure > 60:
                parts.append(f"Fuel pressure is a bit high ({int(pressure)} PSI), could be the pressure regulator.")
            # Don't mention if normal - no news is good news

        return " ".join(parts)

    def humanize_all_codes(self, codes: list, dtc_database: dict) -> str:
        """Create a human-friendly explanation of all codes"""
        if not codes:
            return "Good news, no error codes showing up. Your car's running clean."

        parts = []

        # Opening based on count
        if len(codes) == 1:
            parts.append(f"I found one code to tell you about.")
        else:
            parts.append(f"I found {len(codes)} codes. Let me walk you through them.")

        # Check for related codes
        if "P0300" in codes and "P0171" in codes:
            parts.append("These might actually be connected, by the way. The lean condition could be causing the misfires.")

        # Group by severity
        high = []
        other = []

        for code in codes:
            if code in dtc_database:
                if dtc_database[code]['severity'] == 'HIGH':
                    high.append(code)
                else:
                    other.append(code)

        # Explain high priority first
        if high:
            parts.append("The important one to know about:")
            for code in high:
                info = dtc_database.get(code, {})
                desc = info.get('description', 'Unknown issue')
                parts.append(f"{code} means {desc.lower()}. This one shouldn't wait too long.")

        # Then others
        if other:
            if high:
                parts.append("Also showing:")
            for code in other:
                info = dtc_database.get(code, {})
                desc = info.get('description', 'Unknown issue')
                parts.append(f"{code} is {desc.lower()}. Less urgent, but good to address eventually.")

        # Overall recommendation
        if high:
            parts.append("I'd prioritize the high-priority one first.")
        else:
            parts.append("Nothing here needs immediate attention, but worth keeping on your radar.")

        return " ".join(parts)


# Initialize global humanizer instance
humanizer = ResponseHumanizer()

class NaturalLanguageResponses:
    """Generates natural, human-like conversational responses"""

    @staticmethod
    def vehicle_info(car_data):
        """Friendly vehicle info response"""
        make = (car_data.get('MARK') or 'Unknown').title()
        model = (car_data.get('MODEL') or 'Unknown').title()
        year = car_data.get('CAR_YEAR', 'Unknown')
        engine = car_data.get('ENGINE_POWER', 'Unknown')
        trans = "manual" if car_data.get('AUTOMATIC', 'n') == 'n' else "automatic"
        fuel_type = car_data.get('FUEL_TYPE', 'Unknown').replace('_', '/')

        intros = [
            f"You're driving a {year} {make} {model}.",
            f"Your car is a {year} {make} {model}.",
            f"I see you've got a {year} {make} {model}."
        ]

        response = random.choice(intros)
        engine_str = f"{engine}L" if engine != 'Unknown' else "an unknown engine size"
        response += f" It's got {engine_str} {trans}."

        if fuel_type != "Unknown":
            response += f" Runs on {fuel_type.lower()}."

        return response

    @staticmethod
    def quick_summary(car_data, dtc_database):
        """Human-friendly status summary"""
        codes = car_data.get("TROUBLE_CODES", [])
        fuel = car_data.get("FUEL_LEVEL", 0)
        coolant = car_data.get("ENGINE_COOLANT_TEMP", 80)

        # Determine temperature status
        if coolant < 70:
            temp_status = "cold"
        elif coolant <= 100:
            temp_status = "normal"
        else:
            temp_status = "hot"

        # Check for high priority codes
        has_high = any(dtc_database.get(c, {}).get('severity') == 'HIGH' for c in codes)

        return humanizer.humanize_status(fuel, coolant, temp_status, len(codes), has_high)

    @staticmethod
    def explain_single_dtc(code, dtc_info):
        """Human-friendly DTC code explanation"""
        return humanizer.humanize_code_explanation(
            code=code,
            description=dtc_info['description'],
            severity=dtc_info['severity'],
            causes=dtc_info['possible_causes'],
            cost=dtc_info['estimated_cost']
        )

    @staticmethod
    def explain_all_codes(codes, dtc_database):
        """Human-friendly explanation of all codes"""
        return humanizer.humanize_all_codes(codes, dtc_database)

    @staticmethod
    def engine_status(car_data):
        """Human-friendly engine status"""
        rpm = car_data.get("ENGINE_RPM", 0)
        coolant = car_data.get("ENGINE_COOLANT_TEMP", 0)
        load = car_data.get("ENGINE_LOAD", 0)
        runtime = car_data.get("ENGINE_RUNTIME", "N/A")
        is_running = rpm > 400

        return humanizer.humanize_engine_status(rpm, coolant, load, runtime, is_running)

    @staticmethod
    def fuel_status(car_data):
        """Human-friendly fuel status"""
        fuel_level = car_data.get("FUEL_LEVEL", 0)
        fuel_pressure = car_data.get("FUEL_PRESSURE", 0)

        return humanizer.humanize_fuel_status(fuel_level, fuel_pressure)

    @staticmethod
    def sensor_reading(sensor_name, value, unit=""):
        """Human-friendly sensor reading"""
        friendly_names = {
            'speed': 'speed',
            'rpm': 'engine speed',
            'coolant_temp': 'coolant temperature',
            'fuel_level': 'fuel level',
            'throttle': 'throttle',
            'engine_load': 'engine load',
            'tyre_pressure': 'tyre pressure'
        }

        name = friendly_names.get(sensor_name, sensor_name.replace('_', ' '))

        # Add context based on sensor type
        if sensor_name == 'fuel_level':
            if value > 50:
                return f"Your {name} is at {value}{unit}, plenty in the tank."
            elif value > 25:
                return f"Your {name} is at {value}{unit}, might want to fill up soon."
            else:
                return f"Your {name} is at {value}{unit}, running low."
        elif sensor_name == 'coolant_temp':
            if value < 70:
                return f"Coolant's at {value}{unit}, still warming up."
            elif value <= 100:
                return f"Coolant's at {value}{unit}, perfect temperature."
            else:
                return f"Coolant's at {value}{unit}, running a bit hot."
        else:
            return f"Your {name} is at {value}{unit}."

    @staticmethod
    def temperature_systems(car_data):
        """Human-friendly temperature reading"""
        coolant = car_data.get("ENGINE_COOLANT_TEMP")
        ambient = car_data.get("AMBIENT_AIR_TEMP")
        intake = car_data.get("AIR_INTAKE_TEMP")

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

    @staticmethod
    def maintenance_reminder(component, schedule_info):
        """Human-friendly maintenance reminder"""
        name = component.replace('_', ' ')

        parts = []
        parts.append(f"About your {name}:")
        parts.append(f"Generally you want to service it {schedule_info['interval'].lower()}.")
        parts.append(f"It's {schedule_info['importance'].lower()}.")
        parts.append(f"If it's overdue, you might notice {schedule_info['symptoms_if_overdue'].lower()}.")
        parts.append("Keeping up with this stuff saves money in the long run.")

        return " ".join(parts)

    @staticmethod
    def performance_metrics(car_data):
        """Human-friendly performance metrics"""
        rpm = car_data.get("ENGINE_RPM", 0)
        speed = car_data.get("SPEED", 0)
        load = car_data.get("ENGINE_LOAD", 0)
        throttle = car_data.get("THROTTLE_POS", 0)

        parts = [humanizer.get_greeting()]

        if speed == 0:
            parts.append("You're parked up right now.")
        else:
            parts.append(f"You're moving at {speed} km/h.")

        parts.append(f"Engine's at {rpm} revs, {load}% load, throttle at {throttle}%.")

        if load < 30:
            parts.append("Nice easy driving.")
        elif load < 70:
            parts.append("Normal driving conditions.")
        else:
            parts.append("Engine's working hard, maybe accelerating or going uphill.")

        return " ".join(parts)

    @staticmethod
    def driving_health(car_data, dtc_database):
        """Human-friendly health assessment"""
        issues = []
        good = []

        codes = car_data.get("TROUBLE_CODES", [])
        if codes:
            has_high = any(dtc_database.get(c, {}).get('severity') == 'HIGH' for c in codes)
            if has_high:
                issues.append(f"{len(codes)} code(s), at least one important")
            else:
                issues.append(f"{len(codes)} minor code(s)")
        else:
            good.append("no error codes")

        coolant = car_data.get("ENGINE_COOLANT_TEMP")
        if coolant and coolant > 105:
            issues.append("engine running hot")
        elif coolant and 70 <= coolant <= 100:
            good.append("engine temp normal")

        fuel = car_data.get("FUEL_LEVEL", 50)
        if fuel < 15:
            issues.append("very low fuel")
        elif fuel >= 25:
            good.append("decent fuel level")

        # Build response
        if not issues:
            response = humanizer.get_greeting() + " "
            response += "Everything's looking good. "
            response += ", ".join(good).capitalize() + ". "
            response += "Your car's in good shape."
        else:
            response = humanizer.get_greeting() + " "
            response += "Found a few things to mention. "
            response += "Issues: " + ", ".join(issues) + ". "
            if good:
                response += "But on the plus side: " + ", ".join(good) + "."

        return response
    
class ConversationManager:
    def __init__(self, max_history=3):
        self.history = []
        self.max_history = max_history
        self.structured_context = []  # NEW: Store structured context

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history with optional metadata"""
        message = {"role": role, "content": content}
        if metadata:
            message["metadata"] = metadata

        self.history.append(message)

        # Keep structured context
        if metadata:
            self.structured_context.append({
                "role": role,
                "function": metadata.get("function"),
                "entities": metadata.get("entities", []),
                "topic": metadata.get("topic")
            })

        # Trim history if too long
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]
        if len(self.structured_context) > self.max_history:
            self.structured_context = self.structured_context[-self.max_history:]

    def get_chat_context(self) -> list:
        """Get conversation history for model context"""
        return self.history

    def get_entities_in_context(self) -> list:
        """Get all entities mentioned in recent context"""
        entities = []
        for ctx in self.structured_context:
            entities.extend(ctx.get("entities", []))
        return list(set(entities))  # Unique entities

    def get_recent_topic(self) -> Optional[str]:
        """Get the most recent conversation topic"""
        if self.structured_context:
            return self.structured_context[-1].get("topic")
        return None

    def clear(self):
        """Clear conversation history"""
        self.history = []
        self.structured_context = []

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


class IntentRecognizer:
    """Semantic-based intent recognition using word groups and context"""

    def __init__(self):
        self.dtc_pattern = re.compile(r'\b([PCBU][0-9]{4})\b', re.IGNORECASE)

        # ==========================================
        # SEMANTIC WORD GROUPS
        # ==========================================
        self.semantic_groups = {
            'status_health': [
                'status', 'doing', 'condition', 'health', 'check', 'okay', 'ok',
                'alright', 'fine', 'good', 'state', 'shape', 'running'
            ],
            'error_code': [
                'code', 'codes', 'error', 'errors', 'problem', 'problems',
                'issue', 'issues', 'fault', 'faults', 'wrong', 'dtc',
                'diagnostic', 'trouble', 'warning', 'alert'
            ],
            'engine': [
                'engine', 'motor', 'performance', 'power', 'rpm', 'idle',
                'running', 'start', 'starting'
            ],
            'fuel': [
                'fuel', 'gas', 'petrol', 'diesel', 'tank', 'range', 'mileage'
            ],
            'temperature': [
                'temperature', 'temp', 'hot', 'cold', 'heat', 'coolant',
                'overheating', 'warm', 'cooling'
            ],
            'vehicle_identity': [
                'what car', 'which car', 'what vehicle', 'what model',
                'car info', 'vehicle info', 'about my car', 'my car is',
                'tell me about my car', 'what do i drive', 'what am i driving'
            ],
            'explain': [
                'explain', 'what', 'mean', 'means', 'meaning', 'tell',
                'show', 'describe', 'detail', 'details'
            ],
            'query_words': [
                'how', 'what', 'is', 'are', 'does', 'do', 'any', 'check'
            ],
            'car_references': [
                'car', 'vehicle', 'auto', 'automobile', 'it', 'my'
            ],
            'maintenance': [
                'maintenance', 'service', 'change', 'replace', 'when', 'schedule'
            ]
        }

        # ==========================================
        # INTENT DEFINITIONS WITH SEMANTIC MATCHING
        # ==========================================
        self.intent_definitions = {
            'car_status': {
                'required_groups': ['status_health'],
                'optional_groups': ['car_references', 'query_words'],
                'trigger_phrases': [
                    "how's my car", "hows my car", "how is my car",
                    "car status", "vehicle status", "is my car okay",
                    "is my car ok", "is everything okay", "everything ok",
                    "check my car", "my car doing", "car doing",
                    "is my car fine", "is my car alright", "car health",
                    "how's it doing", "how is it doing", "how's it running"
                ],
                'function': 'get_quick_summary',
                'args': {}
            },
            'vehicle_info': {
                'required_groups': ['vehicle_identity'],
                'optional_groups': [],
                'trigger_phrases': [
                    "what car do i have", "what car is this", "what vehicle",
                    "tell me about my car", "car details", "vehicle details",
                    "what model", "what make", "car information", "vehicle information",
                    "what am i driving", "what do i drive"
                ],
                'function': 'get_vehicle_info',
                'args': {}
            },
            'explain_all_codes': {
                'required_groups': ['error_code'],
                'optional_groups': ['explain', 'query_words'],
                'trigger_phrases': [
                    "what codes", "any codes", "error codes", "what errors",
                    "any errors", "what's wrong", "whats wrong", "any problems",
                    "what problems", "show codes", "list codes", "check codes",
                    "diagnostic codes", "trouble codes", "codes does it have",
                    "does it have codes", "any issues", "what issues",
                    "what faults", "any faults"
                ],
                'function': 'explain_all_active_codes',
                'args': {}
            },
            'engine_status': {
                'required_groups': ['engine'],
                'optional_groups': ['status_health', 'query_words'],
                'trigger_phrases': [
                    "how's my engine", "hows my engine", "how is my engine",
                    "engine status", "engine doing", "engine okay", "engine ok",
                    "check engine", "engine running", "engine condition"
                ],
                'function': 'get_engine_status',
                'args': {}
            },
            'fuel_status': {
                'required_groups': ['fuel'],
                'optional_groups': ['status_health', 'query_words'],
                'trigger_phrases': [
                    "how's my fuel", "fuel level", "how much fuel",
                    "gas level", "fuel status", "check fuel", "fuel left",
                    "how much gas", "tank level"
                ],
                'function': 'get_fuel_status',
                'args': {}
            },
            'temperature_check': {
                'required_groups': ['temperature'],
                'optional_groups': ['status_health', 'query_words'],
                'trigger_phrases': [
                    "check temperature", "temperature status", "how hot",
                    "is it overheating", "coolant temperature", "engine temp"
                ],
                'function': 'check_temperature_systems',
                'args': {}
            },
            'health_check': {
                'required_groups': ['status_health'],
                'optional_groups': ['car_references'],
                'trigger_phrases': [
                    "health check", "health assessment", "overall health",
                    "overall condition", "diagnose my car", "full diagnostic",
                    "complete check"
                ],
                'function': 'assess_driving_health',
                'args': {}
            },
            'performance_metrics': {
                'required_groups': [],
                'optional_groups': [],
                'trigger_phrases': [
                    "performance metrics", "how am i driving", "driving performance",
                    "current performance", "performance data"
                ],
                'function': 'get_performance_metrics',
                'args': {}
            }
        }

    def recognize(self, user_query: str, context: Dict[str, Any] = None) -> Optional[Intent]:
      """Main recognition method using semantic understanding"""
      query_lower = user_query.lower().strip()
      query_words = set(query_lower.split())
      context = context or {}

      # PRIORITY 1: Direct DTC code mention with focus detection
      # This now checks for code AND determines focus (actions/cost/causes/general)
      dtc_intent = self._check_dtc_code(user_query)
      if dtc_intent:
          # Store the code in context for potential follow-ups
          if context is not None:
              context['last_dtc_code'] = dtc_intent.arguments.get('code')
          return dtc_intent

      # PRIORITY 2: Context-based follow-ups (moved up for better handling)
      # Check this early to catch "what should I do?" after discussing a code
      if context:
          context_intent = self._check_context_followup(query_lower, context)
          if context_intent:
              return context_intent

      # PRIORITY 3: Exact trigger phrase matching
      phrase_intent = self._check_trigger_phrases(query_lower)
      if phrase_intent:
          return phrase_intent

      # PRIORITY 4: Semantic group matching
      semantic_intent = self._check_semantic_groups(query_lower, query_words)
      if semantic_intent:
          return semantic_intent

      # PRIORITY 5: Sensor queries
      sensor_intent = self._check_sensor_query(query_lower)
      if sensor_intent:
          return sensor_intent

      # PRIORITY 6: Maintenance queries
      maintenance_intent = self._check_maintenance_query(query_lower)
      if maintenance_intent:
          return maintenance_intent

      # PRIORITY 7: Check for focus keywords without a code (for follow-ups)
      # This catches "what are the recommended actions?" without a code mention
      if context and context.get('last_dtc_code'):
          focus_intent = self._check_focus_followup(query_lower, context)
          if focus_intent:
              return focus_intent

      return None

    def _check_focus_followup(self, query_lower: str, context: Dict[str, Any]) -> Optional[Intent]:
      """Check if user is asking for specific aspect of previously discussed code"""
      last_code = context.get('last_dtc_code')

      if not last_code:
          return None

      # Check for action-related follow-ups
      if any(phrase in query_lower for phrase in [
          'what should i do', 'what to do', 'recommended action',
          'how to fix', 'fix it', 'repair it', 'what action'
      ]):
          return Intent("explain_dtc_code", {"code": last_code, "focus": "actions"})

      # Check for cost-related follow-ups
      if any(phrase in query_lower for phrase in [
          'how much', 'cost', 'price', 'expensive', 'afford'
      ]):
          return Intent("explain_dtc_code", {"code": last_code, "focus": "cost"})

      # Check for cause-related follow-ups
      if any(phrase in query_lower for phrase in [
          'what cause', 'why', 'reason', 'lead to', 'because of'
      ]):
          return Intent("explain_dtc_code", {"code": last_code, "focus": "causes"})

      # Check for "the other one" style references
      if 'other' in query_lower or 'next' in query_lower:
          # Get pending codes from dialog manager if available
          pending = context.get('pending_entities', [])
          if pending and len(pending) > 0:
              next_code = pending[0]
              # Determine focus for the other code
              if any(word in query_lower for word in ['action', 'fix', 'do']):
                  return Intent("explain_dtc_code", {"code": next_code, "focus": "actions"})
              elif any(word in query_lower for word in ['cost', 'price']):
                  return Intent("explain_dtc_code", {"code": next_code, "focus": "cost"})
              else:
                  return Intent("explain_dtc_code", {"code": next_code, "focus": "general"})

      return None

    def _check_dtc_code(self, query):
      """Check if query contains a DTC code AND determine focus"""
      dtc_match = re.search(r'[PBCU]\d{4}', query.upper())
      if dtc_match:
          code = dtc_match.group()
          query_lower = query.lower()

          # Build arguments
          arguments = {"code": code}

          # Detect focus from keywords
          if any(word in query_lower for word in ['action', 'recommend', 'what should', 'fix']):
              arguments["focus"] = "actions"
          elif any(word in query_lower for word in ['cost', 'price', 'expensive']):
              arguments["focus"] = "cost"
          elif any(word in query_lower for word in ['cause', 'why', 'reason']):
              arguments["focus"] = "causes"

          # FIX: Use all 4 required parameters for Intent dataclass
          return Intent(
              name="explain_dtc_code",
              confidence=1.0,
              function_name="explain_dtc_code",
              arguments=arguments
          )

      return None

    def _check_trigger_phrases(self, query_lower: str) -> Optional[Intent]:
        """Check for exact trigger phrases"""
        for intent_name, intent_data in self.intent_definitions.items():
            for phrase in intent_data['trigger_phrases']:
                if phrase in query_lower:
                    return Intent(
                        name=intent_name,
                        confidence=0.95,
                        function_name=intent_data['function'],
                        arguments=intent_data['args'].copy()
                    )
        return None

    def _check_semantic_groups(self, query_lower: str, query_words: set) -> Optional[Intent]:
        """Match query against semantic word groups"""

        # Calculate which semantic groups are present in the query
        group_matches = {}
        for group_name, words in self.semantic_groups.items():
            matches = query_words.intersection(set(words))
            # Also check for multi-word phrases
            phrase_matches = sum(1 for phrase in words if ' ' in phrase and phrase in query_lower)
            group_matches[group_name] = len(matches) + phrase_matches

        # Special handling: Distinguish between status and vehicle info
        # "How's my car?" = status, "What car do I have?" = vehicle info
        if group_matches.get('vehicle_identity', 0) > 0:
            return Intent(
                name='vehicle_info',
                confidence=0.85,
                function_name='get_vehicle_info',
                arguments={}
            )

        # Check for status/health queries about the car
        has_status_words = group_matches.get('status_health', 0) > 0
        has_car_reference = group_matches.get('car_references', 0) > 0
        has_query_word = group_matches.get('query_words', 0) > 0
        has_error_words = group_matches.get('error_code', 0) > 0

        # "How's my car?" pattern - status query
        if has_status_words and has_car_reference and not has_error_words:
            return Intent(
                name='car_status',
                confidence=0.85,
                function_name='get_quick_summary',
                arguments={}
            )

        # "How's my car?" without explicit status words but with "how"
        if 'how' in query_words and has_car_reference and not has_error_words:
            # Check if it's asking about a specific subsystem
            if group_matches.get('engine', 0) > 0:
                return Intent(
                    name='engine_status',
                    confidence=0.85,
                    function_name='get_engine_status',
                    arguments={}
                )
            if group_matches.get('fuel', 0) > 0:
                return Intent(
                    name='fuel_status',
                    confidence=0.85,
                    function_name='get_fuel_status',
                    arguments={}
                )
            # Default "how's my car" to status
            return Intent(
                name='car_status',
                confidence=0.80,
                function_name='get_quick_summary',
                arguments={}
            )

        # Error/code queries
        if has_error_words:
            return Intent(
                name='explain_all_codes',
                confidence=0.85,
                function_name='explain_all_active_codes',
                arguments={}
            )

        # Engine queries
        if group_matches.get('engine', 0) > 0 and has_query_word:
            return Intent(
                name='engine_status',
                confidence=0.80,
                function_name='get_engine_status',
                arguments={}
            )

        # Fuel queries
        if group_matches.get('fuel', 0) > 0 and has_query_word:
            return Intent(
                name='fuel_status',
                confidence=0.80,
                function_name='get_fuel_status',
                arguments={}
            )

        # Temperature queries
        if group_matches.get('temperature', 0) > 0:
            return Intent(
                name='temperature_check',
                confidence=0.80,
                function_name='check_temperature_systems',
                arguments={}
            )

        return None

    def _check_sensor_query(self, query: str) -> Optional[Intent]:
        """Check for sensor-related queries"""
        sensor_map = {
            'fuel level': 'fuel_level',
            'rpm': 'rpm',
            'speed': 'speed',
            'coolant': 'coolant_temp',
            'throttle': 'throttle',
            'engine load': 'engine_load',
            'load': 'engine_load',
            'tyre pressure': 'tyre_pressure',
            'tire pressure': 'tyre_pressure'
        }

        for sensor_phrase, sensor_name in sensor_map.items():
            if sensor_phrase in query:
                if any(word in query for word in ['what', 'show', 'tell', 'current', 'reading', 'level', 'how', 'my']):
                    return Intent(
                        name='get_sensor_reading',
                        confidence=0.85,
                        function_name='get_live_sensor_reading',
                        arguments={'sensor_name': sensor_name}
                    )
        return None

    def _check_maintenance_query(self, query: str) -> Optional[Intent]:
        """Check for maintenance-related queries"""
        if not any(word in query for word in ['when', 'maintenance', 'service', 'change', 'replace', 'should i']):
            return None

        maintenance_map = {
            'oil': 'oil',
            'air filter': 'air_filter',
            'brake': 'brake_pads',
            'tyre': 'tyres',
            'tire': 'tyres',
            'coolant': 'coolant',
            'spark plug': 'spark_plugs',
            'battery': 'battery'
        }

        for keyword, component in maintenance_map.items():
            if keyword in query:
                return Intent(
                    name='maintenance_reminder',
                    confidence=0.85,
                    function_name='get_maintenance_reminder',
                    arguments={'component': component}
                )
        return None

    def _check_context_followup(self, query_lower: str, context: Dict[str, Any]) -> Optional[Intent]:
        """Enhanced: Check for follow-up questions using context"""

        # Strong explicit indicators
        explicit_followup = ['that', 'it', 'this', 'the code', 'same', 'these', 'those', 'them', 'they']
        parallel_phrases = ['and for', 'what about', 'how about', 'and what about']
        possessive_refs = [
            'that problem', 'those problems', 'that issue', 'those issues',
            'the problem', 'the problems', 'the issue', 'the issues',
            'the error', 'the errors', 'the code', 'the codes',
            'my problem', 'my issue', 'my error', 'my code'
        ]
        implicit_followup = ['the', 'my']

        has_explicit_followup = any(indicator in query_lower for indicator in explicit_followup)
        has_parallel = any(phrase in query_lower for phrase in parallel_phrases)
        has_possessive = any(ref in query_lower for ref in possessive_refs)
        has_implicit_followup = any(indicator in query_lower.split()[:3] for indicator in implicit_followup)

        is_followup = has_explicit_followup or has_parallel or has_possessive

        if not is_followup and has_implicit_followup and context.get('last_dtc_code'):
            followup_keywords = [
                'cost', 'price', 'expensive', 'how much', 'repair', 'fix',
                'action', 'do', 'cause', 'why', 'problem', 'issue', 'mean'
            ]
            if any(keyword in query_lower for keyword in followup_keywords):
                is_followup = True

        # DTC CODE FOLLOW-UPS WITH FOCUS PARAMETER
        if is_followup and context.get('last_dtc_code'):
            code = context['last_dtc_code']

            # Cost-related questions → focus="cost"
            cost_keywords = ['cost', 'price', 'expensive', 'how much', 'pay', 'spend', 'money', 'budget']
            if any(keyword in query_lower for keyword in cost_keywords):
                return Intent(
                    name='explain_dtc_cost',
                    confidence=0.90,
                    function_name='explain_dtc_code',
                    arguments={'code': code, 'focus': 'cost'}
                )

            # Action/repair-related questions → focus="actions"
            action_keywords = ['recommend', 'recommendation', 'action', 'should i do', 'fix', 'repair',
                              'what to do', 'do about', 'how to fix', 'solve', 'address', 'steps',
                              'what should', 'how do i', 'what can i']
            if any(keyword in query_lower for keyword in action_keywords):
                return Intent(
                    name='explain_dtc_action',
                    confidence=0.90,
                    function_name='explain_dtc_code',
                    arguments={'code': code, 'focus': 'actions'}
                )

            # Cause-related questions → focus="causes"
            cause_keywords = ['cause', 'causes', 'why', 'reason', 'what caused', 'trigger', 'triggered']
            if any(keyword in query_lower for keyword in cause_keywords):
                return Intent(
                    name='explain_dtc_cause',
                    confidence=0.90,
                    function_name='explain_dtc_code',
                    arguments={'code': code, 'focus': 'causes'}
                )

            # Meaning/general questions → focus="general"
            meaning_keywords = ['mean', 'means', 'meaning', 'indicate', 'indicates']
            if any(keyword in query_lower for keyword in meaning_keywords):
                return Intent(
                    name='explain_dtc_meaning',
                    confidence=0.85,
                    function_name='explain_dtc_code',
                    arguments={'code': code, 'focus': 'general'}
                )

            # Severity questions → focus="general" (includes severity info)
            severity_keywords = ['serious', 'urgent', 'bad', 'dangerous', 'safe', 'drive', 'important']
            if any(keyword in query_lower for keyword in severity_keywords):
                return Intent(
                    name='explain_dtc_severity',
                    confidence=0.85,
                    function_name='explain_dtc_code',
                    arguments={'code': code, 'focus': 'general'}
                )

            # General problem questions → focus="general"
            general_keywords = ['problem', 'issue', 'error', 'trouble', 'wrong', 'fault']
            if any(keyword in query_lower for keyword in general_keywords):
                return Intent(
                    name='explain_dtc_general',
                    confidence=0.80,
                    function_name='explain_dtc_code',
                    arguments={'code': code, 'focus': 'general'}
                )

        # FOLLOW-UP AFTER QUICK SUMMARY
        if context.get('last_function') == 'get_quick_summary':
            code_related = ['code', 'error', 'trouble', 'dtc', 'diagnostic', 'issue', 'problem']
            explain_words = ['explain', 'show', 'tell', 'what', 'list', 'check', 'detail', 'mean', 'means']

            has_code_word = any(word in query_lower for word in code_related)
            has_explain_word = any(word in query_lower for word in explain_words)

            if has_code_word or has_explain_word:
                return Intent(
                    name='explain_all_codes',
                    confidence=0.85,
                    function_name='explain_all_active_codes',
                    arguments={}
                )

        # FOLLOW-UP AFTER EXPLAIN ALL CODES
        if context.get('last_function') == 'explain_all_active_codes':
            # Check if asking about meaning of ALL codes (using "they")
            they_meaning = ['what do they mean', 'what they mean', 'do they mean', 'explain them']
            if any(phrase in query_lower for phrase in they_meaning):
                return Intent(
                    name='explain_all_codes',
                    confidence=0.90,
                    function_name='explain_all_active_codes',
                    arguments={}
                )

            # Check for general meaning questions
            meaning_keywords = ['mean', 'means', 'meaning', 'what do', 'what does', 'explain', 'detail']
            if any(keyword in query_lower for keyword in meaning_keywords):
                # If "they" or "them" is in query, explain all codes
                if 'they' in query_lower or 'them' in query_lower:
                    return Intent(
                        name='explain_all_codes',
                        confidence=0.85,
                        function_name='explain_all_active_codes',
                        arguments={}
                    )
                # Otherwise explain the last discussed code
                if context.get('last_dtc_code'):
                    return Intent(
                        name='explain_dtc',
                        confidence=0.85,
                        function_name='explain_dtc_code',
                        arguments={'code': context['last_dtc_code']}
                    )
                return Intent(
                    name='explain_all_codes',
                    confidence=0.85,
                    function_name='explain_all_active_codes',
                    arguments={}
                )

        # VAGUE FOLLOW-UP QUERIES
        vague_queries = [
            'what about it', 'tell me more', 'more info', 'more information',
            'what else', 'anything else', 'more details', 'explain more',
            'tell me', 'elaborate'
        ]

        if any(vague in query_lower for vague in vague_queries):
            last_func = context.get('last_function')

            if last_func == 'explain_dtc_code' and context.get('last_dtc_code'):
                return Intent(
                    name='explain_dtc_repeat',
                    confidence=0.75,
                    function_name='explain_dtc_code',
                    arguments={'code': context['last_dtc_code']}
                )
            elif last_func == 'explain_all_active_codes':
                return Intent(
                    name='explain_all_codes_repeat',
                    confidence=0.75,
                    function_name='explain_all_active_codes',
                    arguments={}
                )
            elif last_func == 'assess_driving_health':
                return Intent(
                    name='health_repeat',
                    confidence=0.75,
                    function_name='assess_driving_health',
                    arguments={}
                )

        return None 
    
class DynamicOBDHandler:
    """Handles dynamic OBD queries with natural language responses"""

    def __init__(self, car_data, sensor_ranges=None):
        self.car_data = car_data
        self.sensor_ranges = sensor_ranges or SENSOR_RANGES

        # Semantic mappings for common terms
        self.semantic_map = {
            'fuel': ['FUEL_LEVEL', 'FUEL_PRESSURE', 'FUEL_TYPE'],
            'temperature': ['ENGINE_COOLANT_TEMP', 'AMBIENT_AIR_TEMP', 'AIR_INTAKE_TEMP'],
            'coolant': ['ENGINE_COOLANT_TEMP'],
            'pressure': ['BAROMETRIC_PRESSURE', 'FUEL_PRESSURE', 'INTAKE_MANIFOLD_PRESSURE', 'TYRE_PRESSURE'],
            'engine': ['ENGINE_RPM', 'ENGINE_LOAD', 'ENGINE_RUNTIME', 'ENGINE_POWER'],
            'tire': ['TYRE_PRESSURE'],
            'tyre': ['TYRE_PRESSURE'],
        }

    def find_relevant_parameters(self, query):
        """Find OBD parameters relevant to the query"""
        query_lower = query.lower()
        relevant_params = []

        # Check semantic mappings
        for keyword, params in self.semantic_map.items():
            if keyword in query_lower:
                for param in params:
                    if param in self.car_data and param not in relevant_params:
                        relevant_params.append(param)

        return relevant_params

    def assess_value(self, param, value):
        """Assess if a value is normal, low, or high"""
        if param in self.sensor_ranges:
            range_info = self.sensor_ranges[param]
            min_val = range_info.get('min', float('-inf'))
            max_val = range_info.get('max', float('inf'))

            if value < min_val:
                return "low"
            elif value > max_val:
                return "high"
            else:
                return "normal"
        return "normal"

    def generate_response(self, query):
        """Generate natural, conversational response based on query"""
        relevant_params = self.find_relevant_parameters(query)

        if not relevant_params:
            return None

        query_lower = query.lower()

        # FUEL queries - conversational style
        if 'fuel' in query_lower:
            fuel_level = self.car_data.get('FUEL_LEVEL', 0)
            fuel_pressure = self.car_data.get('FUEL_PRESSURE', 0)
            fuel_type = self.car_data.get('FUEL_TYPE', 'Unknown').replace('_', '/')

            response = ""

            # Fuel level assessment
            if fuel_level >= 60:
                response = f"Your fuel's looking good at {fuel_level:.0f}%. "
            elif fuel_level >= 40:
                response = f"You're at {fuel_level:.0f}% fuel, so you might want to fill up soon. "
            elif fuel_level >= 25:
                response = f"Getting a bit low at {fuel_level:.0f}%, definitely plan a fuel stop. "
            else:
                response = f"Running pretty low at {fuel_level:.0f}%, I'd refuel soon. "

            # Add pressure if it's abnormal
            pressure_status = self.assess_value('FUEL_PRESSURE', fuel_pressure)
            if pressure_status == "low":
                response += f"Your fuel pressure is a bit low at {fuel_pressure} PSI, might want to have that checked. "
            elif pressure_status == "high":
                response += f"Fuel pressure is higher than normal at {fuel_pressure} PSI. "
            else:
                response += f"Fuel pressure is normal at {fuel_pressure} PSI. "

            # Mention fuel type
            response += f"By the way, your car runs on {fuel_type}."

            return response.strip()

        # TEMPERATURE queries
        elif 'temp' in query_lower or 'coolant' in query_lower:
            coolant = self.car_data.get('ENGINE_COOLANT_TEMP', 0)
            ambient = self.car_data.get('AMBIENT_AIR_TEMP', 0)

            response = ""

            if 80 <= coolant <= 100:
                response = f"Engine temperature is perfect at {coolant}°C. "
            elif coolant < 80:
                response = f"Engine's still warming up, currently at {coolant}°C. "
            else:
                response = f"Engine's running a bit hot at {coolant}°C, keep an eye on that. "

            if ambient:
                response += f"Outside temperature is {ambient}°C."

            return response.strip()

        # PRESSURE queries
        elif 'pressure' in query_lower:
            tire_pressure = self.car_data.get('TYRE_PRESSURE', 0)
            fuel_pressure = self.car_data.get('FUEL_PRESSURE', 0)

            response = "Let me check your pressures. "

            if tire_pressure:
                if 70 <= tire_pressure <= 100:
                    response += f"Tire pressure is good at {tire_pressure} PSI. "
                else:
                    response += f"Tire pressure is {tire_pressure} PSI, might need adjustment. "

            if fuel_pressure:
                if 30 <= fuel_pressure <= 60:
                    response += f"Fuel pressure is normal at {fuel_pressure} PSI."
                else:
                    response += f"Fuel pressure is {fuel_pressure} PSI."

            return response.strip()

        # ENGINE queries
        elif 'engine' in query_lower:
            rpm = self.car_data.get('ENGINE_RPM', 0)
            load = self.car_data.get('ENGINE_LOAD', 0)
            runtime = self.car_data.get('ENGINE_RUNTIME', 'Unknown')

            response = f"Your engine's running at {rpm} RPM "

            if load < 50:
                response += f"with a comfortable {load:.0f}% load. "
            else:
                response += f"working at {load:.0f}% capacity. "

            if runtime != 'Unknown':
                response += f"It's been running for {runtime}."

            return response.strip()

        # Single parameter query
        elif len(relevant_params) == 1:
            param = relevant_params[0]
            value = self.car_data[param]
            param_readable = param.replace('_', ' ').lower()

            # Make it conversational
            if isinstance(value, (int, float)):
                status = self.assess_value(param, value)
                if status == "normal":
                    return f"Your {param_readable} is {value}, which looks normal."
                elif status == "low":
                    return f"Your {param_readable} is {value}, which is a bit low."
                else:
                    return f"Your {param_readable} is {value}, which is higher than usual."
            else:
                return f"Your {param_readable} is {value}."

        # Multiple parameters - still make it conversational
        else:
            response = "Here's what I found: "
            for i, param in enumerate(relevant_params):
                value = self.car_data[param]
                param_readable = param.replace('_', ' ').lower()

                if i == len(relevant_params) - 1 and i > 0:
                    response += f"and your {param_readable} is {value}."
                elif i > 0:
                    response += f"your {param_readable} is {value}, "
                else:
                    response += f"your {param_readable} is {value}, "

            return response
        
# Maintenance schedule data
MAINTENANCE_SCHEDULE = {
    "oil": {
        "interval": "Every 5,000-7,500 miles or 6 months",
        "importance": "Critical for engine longevity",
        "symptoms_if_overdue": "Engine knocking, reduced performance, check engine light"
    },
    "air_filter": {
        "interval": "Every 15,000-30,000 miles",
        "importance": "Maintains engine efficiency",
        "symptoms_if_overdue": "Reduced fuel economy, sluggish acceleration"
    },
    "brake_pads": {
        "interval": "Every 25,000-70,000 miles",
        "importance": "Critical for safety",
        "symptoms_if_overdue": "Squealing noise, reduced braking performance"
    },
    "tyres": {
        "interval": "Check monthly, rotate every 5,000-8,000 miles",
        "importance": "Safety and fuel efficiency",
        "symptoms_if_overdue": "Uneven wear, poor handling, reduced fuel economy"
    },
    "coolant": {
        "interval": "Every 30,000-50,000 miles or 2-3 years",
        "importance": "Prevents engine overheating",
        "symptoms_if_overdue": "Engine overheating, sweet smell from engine"
    },
    "spark_plugs": {
        "interval": "Every 30,000-100,000 miles (depends on type)",
        "importance": "Ensures proper combustion",
        "symptoms_if_overdue": "Misfires, rough idle, reduced fuel economy"
    },
    "battery": {
        "interval": "Every 3-5 years",
        "importance": "Reliable starting and electrical system",
        "symptoms_if_overdue": "Slow engine crank, dim lights, electrical issues"
    }
}

# Initialize NLG
nlg = NaturalLanguageResponses()

def get_vehicle_info(car_data):
    """Get basic vehicle information with natural response"""
    return nlg.vehicle_info(car_data)

def get_quick_summary(car_data):
    """Get a quick summary of all major systems"""
    return nlg.quick_summary(car_data, DTC_DATABASE)

def explain_dtc_code(car_data, code, focus="general"):
    """
    Explain a specific DTC code with optional focus on specific aspect.
    """
    code = code.upper().strip()

    if code not in DTC_DATABASE:
        available = ', '.join(DTC_DATABASE.keys())
        return (
            f"Hmm, I don't have information about code {code} in my database. "
            f"Make sure it's typed correctly (like P0300). Codes I know about: {available}"
        )

    # car_data not strictly needed here, but we keep it in signature for consistency
    return humanizer.humanize_code_explanation_with_focus(code, DTC_DATABASE, focus=focus)

def query_obd_data(car_data, query_type=None, parameters=None):
    """Universal handler for OBD data queries"""
    handler = DynamicOBDHandler(car_data, SENSOR_RANGES)

    if query_type == "fuel":
        return handler.generate_response("fuel information")
    elif query_type == "temperature":
        return handler.generate_response("temperature readings")
    elif query_type == "pressure":
        return handler.generate_response("pressure readings")
    elif query_type == "engine":
        return handler.generate_response("engine status")
    elif query_type == "specific" and parameters:
        param_name = parameters.get("parameter_name", "")
        if param_name in car_data:
            value = car_data[param_name]
            readable = param_name.replace('_', ' ').lower()
            return f"Your {readable} is {value}."

    if query_type:
        response = handler.generate_response(query_type)
        if response:
            return response

    return "I couldn't find that information in your vehicle data."

def explain_all_active_codes(car_data):
    """Get detailed explanations for all active codes"""
    codes = car_data.get("TROUBLE_CODES", [])
    return nlg.explain_all_codes(codes, DTC_DATABASE)

def get_engine_status(car_data):
    """Get engine status in natural language"""
    return nlg.engine_status(car_data)

def get_fuel_status(car_data):
    """Get fuel status in natural language"""
    return nlg.fuel_status(car_data)

def get_live_sensor_reading(car_data, sensor_name):
    """Get a sensor reading in natural language"""
    sensor_map = {
        "speed": ("SPEED", "km/h"),
        "rpm": ("ENGINE_RPM", "RPM"),
        "coolant_temp": ("ENGINE_COOLANT_TEMP", "°C"),
        "fuel_level": ("FUEL_LEVEL", "%"),
        "throttle": ("THROTTLE_POS", "%"),
        "engine_load": ("ENGINE_LOAD", "%"),
        "tyre_pressure": ("TYRE_PRESSURE", "PSI")
    }

    sensor_name = sensor_name.lower().replace(" ", "_")

    if sensor_name not in sensor_map:
        available = ", ".join(sensor_map.keys())
        return f"I don't recognise that sensor. Try asking about: {available}"

    key, unit = sensor_map[sensor_name]
    value = car_data.get(key)

    if value is None:
        return f"Sorry, {sensor_name.replace('_', ' ')} data isn't available right now."

    # NOTE: your nlg.sensor_reading signature might differ.
    # If your NaturalLanguageResponses.sensor_reading expects (param, value, assessment),
    # then this should be adjusted. Keeping your original call for now:
    return nlg.sensor_reading(sensor_name, value, unit)

def check_temperature_systems(car_data):
    """Check temperature systems in natural language"""
    return nlg.temperature_systems(car_data)

def get_maintenance_reminder(car_data, component):
    """Get maintenance reminder in natural language"""
    component = component.lower().replace(" ", "_")

    if component not in MAINTENANCE_SCHEDULE:
        available = ", ".join(MAINTENANCE_SCHEDULE.keys())
        return f"I don't have maintenance info for '{component}'. Try asking about: {available}"

    return nlg.maintenance_reminder(component, MAINTENANCE_SCHEDULE[component])

def get_performance_metrics(car_data):
    """Get performance metrics in natural language"""
    return nlg.performance_metrics(car_data)

def assess_driving_health(car_data):
    """Comprehensive health assessment in natural language"""
    return nlg.driving_health(car_data, DTC_DATABASE)

def explain_multiple_codes(codes: list) -> str:
    """Explain multiple DTC codes in a human-friendly way"""
    if not codes:
        return "No codes to explain."

    parts = []

    if len(codes) == 2:
        parts.append("Let me explain both of those for you.")
    else:
        parts.append(f"Let me walk you through all {len(codes)} codes.")

    for i, code in enumerate(codes):
        code = code.upper().strip()
        if code in DTC_DATABASE:
            info = DTC_DATABASE[code]

            explanation = humanizer.humanize_code_explanation(
                code=code,
                description=info['description'],
                severity=info['severity'],
                causes=info['possible_causes'],
                cost=info['estimated_cost']
            )

            if i > 0:
                transitions = ["Next up,", "Also,", "And then there's,", "Moving on,"]
                parts.append(random.choice(transitions))

            parts.append(explanation)
        else:
            parts.append(f"{code}: I don't have that one in my database, sorry.")

    return " ".join(parts)

def handle_off_topic():
    return "I'm designed to help with car diagnostics only. Is there anything about your vehicle I can help with?"


def make_function_registry(car_data):
    """
    Build a registry bound to this request's car_data.
    This avoids global state and is safe for multiple users.
    """
    return {
        "get_vehicle_info": lambda: get_vehicle_info(car_data),
        "get_quick_summary": lambda: get_quick_summary(car_data),
        "explain_dtc_code": lambda code, focus="general": explain_dtc_code(car_data, code, focus),
        "explain_all_active_codes": lambda: explain_all_active_codes(car_data),
        "explain_multiple_codes": explain_multiple_codes,  # does not need car_data
        "get_engine_status": lambda: get_engine_status(car_data),
        "get_fuel_status": lambda: get_fuel_status(car_data),
        "get_live_sensor_reading": lambda sensor_name: get_live_sensor_reading(car_data, sensor_name),
        "check_temperature_systems": lambda: check_temperature_systems(car_data),
        "get_maintenance_reminder": lambda component: get_maintenance_reminder(car_data, component),
        "get_performance_metrics": lambda: get_performance_metrics(car_data),
        "assess_driving_health": lambda: assess_driving_health(car_data),
        "query_obd_data": lambda query_type=None, parameters=None: query_obd_data(car_data, query_type, parameters),
        "handle_off_topic": handle_off_topic
    }


def build_enhanced_system_prompt(car_data=None, dialog_manager=None):
    """Optimized prompt - same functionality, fewer tokens"""
    entities_discussed = []

    dynamic_context = ""
    available_params = []

    if car_data:
        codes = car_data.get('TROUBLE_CODES', [])
        if codes:
            codes_with_severity = [f"{c}({DTC_DATABASE.get(c, {}).get('severity', '?')})" for c in codes]
            dynamic_context += f"Active Codes: {', '.join(codes_with_severity)}\n"
        else:
            dynamic_context += "Active Codes: None\n"

        dynamic_context += f"Fuel: {car_data.get('FUEL_LEVEL', 0):.0f}% | Temp: {car_data.get('ENGINE_COOLANT_TEMP', 0)}°C | Tires: {car_data.get('TYRE_PRESSURE', 0)} PSI\n"

        if dialog_manager:
        # dialog_manager might be a DialogManager object OR a dict OR something else.
         entities_discussed = []
        last_code = None

        # If it's an object with attributes
        if hasattr(dialog_manager, "entities_discussed"):
            entities_discussed = dialog_manager.entities_discussed or []
        if hasattr(dialog_manager, "last_dtc_code"):
            last_code = dialog_manager.last_dtc_code

        # If it's a dict (fallback)
        if isinstance(dialog_manager, dict):
            entities_discussed = dialog_manager.get("entities_discussed", entities_discussed) or []
            last_code = dialog_manager.get("last_dtc_code", last_code)

        if entities_discussed:
            dynamic_context += f"Discussed: {', '.join(entities_discussed)}\n"
        if last_code:
            dynamic_context += f"Last Code: {last_code}\n"
 
        available_params = [k for k in car_data.keys()
                          if k not in ['TROUBLE_CODES', 'TIMESTAMP', 'VEHICLE_ID', 'MARK', 'MODEL', 'CAR_YEAR']]

    param_sample = ", ".join(available_params[:8]) if available_params else "None"

    prompt = f'''Car diagnostic assistant. Return JSON only. Redirect non-car topics politely.

=== VEHICLE STATE ===
{dynamic_context}OBD Params: {param_sample}

=== ROUTING RULES ===
Greetings (hi/hello) → {{"name": "greet_user", "arguments": {{}}}}
Car status → {{"name": "get_quick_summary", "arguments": {{}}}}
What car? → {{"name": "get_vehicle_info", "arguments": {{}}}}
List codes → {{"name": "explain_all_active_codes", "arguments": {{}}}}

DTC Code queries (P0XXX):
- explain/what is → {{"name": "explain_dtc_code", "arguments": {{"code": "P0XXX", "focus": "general"}}}}
- fix/actions → {{"name": "explain_dtc_code", "arguments": {{"code": "P0XXX", "focus": "actions"}}}}
- cost/price → {{"name": "explain_dtc_code", "arguments": {{"code": "P0XXX", "focus": "cost"}}}}
- cause/why → {{"name": "explain_dtc_code", "arguments": {{"code": "P0XXX", "focus": "causes"}}}}

Sensors:
- engine status → {{"name": "get_engine_status", "arguments": {{}}}}
- fuel status → {{"name": "get_fuel_status", "arguments": {{}}}}
- temperatures → {{"name": "check_temperature_systems", "arguments": {{}}}}
- specific sensor → {{"name": "get_live_sensor_reading", "arguments": {{"sensor_name": "SENSOR_NAME"}}}}
- fuel/temp/pressure/speed → {{"name": "query_obd_data", "arguments": {{"query_type": "TYPE"}}}}
- specific param → {{"name": "query_obd_data", "arguments": {{"query_type": "specific", "parameters": {{"parameter_name": "NAME"}}}}}}

Other:
- maintenance → {{"name": "get_maintenance_reminder", "arguments": {{"component": "COMPONENT"}}}}
- performance → {{"name": "get_performance_metrics", "arguments": {{}}}}
- full diagnostic → {{"name": "assess_driving_health", "arguments": {{}}}}

=== CONTEXT RULES ===
"it/that/this" → Use Last Code
"how much?" (no code) → Last Code + focus=cost
"fix it?" (no code) → Last Code + focus=actions
"the other one" → Next code not in Discussed

=== OUTPUT ===
JSON only: {{"name": "function", "arguments": {{}}}}'''

    return prompt

def truncate_prompt_to_ctx(prompt: str, n_ctx: int, reserve: int = 200) -> str:
    """
    Ensure prompt fits into llama.cpp context window.
    reserve = tokens kept free for the model's response.
    """
    tokens = llm.tokenize(prompt.encode("utf-8"))
    max_prompt_tokens = max(0, n_ctx - reserve)

    if len(tokens) <= max_prompt_tokens:
        return prompt

    # Keep the most recent part of the prompt (drops oldest tokens first)
    truncated_tokens = tokens[-max_prompt_tokens:]
    return llm.detokenize(truncated_tokens).decode("utf-8", errors="ignore")

def get_model_response_with_context(
    user_query: str,
    history: list,
   # conversation_manager,
    car_data: dict,
    dialog_manager=None,
    dynamic_handler=None
):
    # 1) Build system prompt using THIS request's car_data
    system_prompt = build_enhanced_system_prompt(car_data, dialog_manager)

    # 2) Build prompt from short history
    #history = conversation_manager.get_chat_context()

    history_text = ""
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        history_text += f"{role.upper()}: {content}\n"

    prompt = (
        f"SYSTEM:\n{system_prompt}\n\n"
        f"{history_text}"
        f"USER: {user_query}\n"
        f"ASSISTANT: Return ONLY valid JSON for the function call."
    )

    # 3) Generate with llama.cpp
    try:
        llm.reset()
    except AttributeError:
        pass

    prompt = truncate_prompt_to_ctx(prompt, n_ctx=1024, reserve=220)

    result = llm(
        prompt,
        max_tokens=160,      # keep small
        temperature=0.2,
        top_p=0.95,
        stop=["USER:", "SYSTEM:"]
    )

    # ✅ print memory AFTER generation (per request)
    print_memory_usage("after generation")

    raw_text = result["choices"][0]["text"].strip()

    # 4) Parse JSON tool call
    try:
        tool_call = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            return "Sorry — I couldn't understand that. Try asking in a different way."
        tool_call = json.loads(match.group(0))

    # 5) Execute tool call using per-request registry
    name = tool_call.get("name")
    args = tool_call.get("arguments", {}) or {}

    registry = make_function_registry(car_data)

    if name not in registry:
        return "Sorry — I generated an unknown action. Try asking another way."

    try:
        response = registry[name](**args)
        return humanizer.remove_jargon(response)
    except Exception as e:
        return f"Something went wrong running {name}: {e}"

print_memory_usage("after generation")

def extract_function_call(response):
    """Extract JSON function call from model response"""
    if not response:
        return None

    # Clean the response
    response = response.strip()

    # Remove common prefixes that models add
    for prefix in ["Assistant:", "InsightBot:", "Response:", "Answer:"]:
        if prefix in response:
            response = response.split(prefix)[-1].strip()

    # Try direct JSON parsing first
    try:
        data = json.loads(response)
        if 'name' in data:
            return json.dumps(data)  # Return as string for consistency
    except:
        pass

    # Look for JSON patterns
    patterns = [
        r'\{[^{}]*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\}',
        r'\{[^{}]*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{\}\}',
        r'\{"name"[^}]+\}'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            try:
                # Validate it's proper JSON
                json.loads(matches[-1])
                return matches[-1]
            except:
                continue

    # Check if the entire response might be wrapped
    if '{' in response and '}' in response:
        start = response.index('{')
        end = response.rindex('}') + 1
        potential_json = response[start:end]
        try:
            data = json.loads(potential_json)
            if 'name' in data:
                return potential_json
        except:
            pass

    return None


def handle_function_call(json_text):
    """Execute the appropriate function based on JSON input"""
    try:
        data = json.loads(json_text)
        func_name = data.get("name")
        args = data.get("arguments", {})

        if func_name not in make_function_registry:
            return "I'm not sure how to help with that. Try asking about your car status, error codes, or fuel level."

        response = make_function_registry[func_name](**args)

        response = humanizer.remove_jargon(response)

        return response

    except json.JSONDecodeError:
        return "I had trouble understanding that. Could you try asking differently?"
    except TypeError as e:
        return "Something went wrong with that request. Mind rephrasing?"
    except Exception as e:
        return "Oops, hit a snag there. What would you like to know about your car?"