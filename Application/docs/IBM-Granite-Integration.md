# IBM Granite AI Integration

This document describes the planned integration of IBM Granite AI into the IBM OBD InsightBot system.

**Current Status**:
- IBM Granite Model "IBM Granite-4.0-h-1b" created and integrated into ASP .NET webapp hosted on a Virtual machine


## Overview

IBM OBD InsightBot will use IBM Granite AI for:
- Natural language understanding of diagnostic queries (FR-01)
- Plain-language explanations of technical DTC codes (FR-02)
- Conversational context management (FR-03)
- Function calling for structured diagnostic operations (FR-04)

**What Exists Now**: IBM Granite Model "IBM Granite-4.0-h-1b" created and integrated into ASP .NET webapp hosted on a Virtual machine


## IBM Granite Model

### Previous Experimentation

**Model Being Tested**: IBM Granite 1B

**Where**: Jupyter notebooks only

**Purpose**: Understanding model capabilities and behavior before production integration

### Production Model

**Model**: IBM Granite 1B

**Reason for 1B Model**:
- VM resource constraints (low RAM, CPU only - no GPU)
- Smaller model suitable for available infrastructure
- Balances performance with resource limitations

**Key Capabilities**:
- Instruction following
- Basic conversational context
- Automotive domain understanding (general knowledge)

**Note**: Larger models (3B, 8B) would require more RAM and ideally GPU acceleration, which exceeds current VM capabilities

## Previous Experimentation (Jupyter Notebooks)

### What We're Testing

In Jupyter notebooks, we are exploring:
- Basic prompt engineering
- Response quality for automotive queries
- Model behavior with diagnostic scenarios
- Context handling across multiple turns

### Example Notebook Experiments

**Basic Query Testing**:
```python
# Example from Jupyter notebook experimentation
# This is NOT production code

prompt = "Explain what DTC code P0301 means in simple terms"
response = model.generate(prompt)
# Testing response quality and clarity
```

**Context Testing**:
```python
# Testing conversation context
conversation = [
    {"role": "user", "content": "What is P0301?"},
    {"role": "assistant", "content": "...previous response..."},
    {"role": "user", "content": "Is it serious?"}
]
# Testing if model maintains context
```

## Planned Integration Architecture

### High-Level Plan

```
User Query
    ↓
[Backend Service]
    ↓
[Granite AI Integration]
    ↓
Self-Hosted Granite Model - HOSTING TBD
    ↓
Response Processing
    ↓
User Response
```

**Current Status**: Implementation finished

### Hosting Approach

**Decided**: VM-based hosting with resource constraints

**Infrastructure Constraints**:
- Low RAM availability
- CPU only (no GPU)
- Limited to smaller models

**Model Selection**:
- Using Granite 1B model
- Optimized for CPU inference
- Fits within VM memory constraints

**Trade-offs**:
- Smaller model means faster inference on limited hardware
- May have reduced accuracy compared to larger models
- Good enough for prototype/academic project requirements

## Integration Approach (Complete)

### What Needs to Be Built

1. **Model Hosting Infrastructure**
   - Deploy Granite 1B model on VM (CPU-only)
   - Set up inference endpoint
   - Optimize for limited RAM environment

2. **Backend Integration Service**
   - C# service to communicate with hosted model
   - Request/response handling
   - Error handling and retry logic

3. **Prompt Engineering**
   - System prompts for automotive context
   - Conversation context management
   - Function calling schema (if supported by chosen model)

4. **Response Processing**
   - Parse model outputs
   - Format for frontend display
   - Handle edge cases

**Current Status**: Completed

## Prompt Engineering Strategy

### System Prompt Design

Will need to define AI behavior:

```
You are an automotive diagnostic assistant.
Help users understand OBD-II diagnostic data in plain language.
Focus on vehicle diagnostics only.
Always include safety disclaimers for serious issues.
```

### Context Management 

Will need to:
- Store conversation history per session (FR-03)
- Include recent exchanges in prompts
- Clear context when session ends (RNF-03)

**Current Status**: Completed

### Function Calling 

Based on FR-04, will need to support functions like:
- `get_quick_summary()` - Overall vehicle status
- `explain_dtc_code(code)` - Specific DTC explanation
- `explain_all_active_codes()` - All active DTCs
- `get_sensor_reading(sensor)` - Sensor values
- `get_engine_status()` - Engine health
- `get_fuel_status()` - Fuel system status
- `get_vehicle_info()` - Vehicle details

**Current Status**: Completed

## Model Configuration Parameters

### Typical Parameters for Text Generation

Once implemented, will likely need to configure:

- **max_new_tokens**: Response length limit (e.g., 500)
- **temperature**: Randomness (0.7 for balanced responses)
- **top_p**: Nucleus sampling threshold (0.9)
- **top_k**: Token selection range (50)

**Note**: Actual values to be determined through testing

## Requirements Alignment

### Performance (RNF-01)
**Requirement**: 90% of queries complete within 3 seconds

**Considerations**:
- Model size vs. speed tradeoff
- Hosting infrastructure performance
- Network latency

**Status**: Completed

### Accuracy (RNF-05)
**Requirement**: 85% intent detection accuracy

**Plan**:
- Manual evaluation of sample responses
- Iterative prompt refinement

**Status**: Will be tested during implementation

### Safety (RNF-02)
**Requirement**: Prominent safety disclaimers

**Plan**:
- Include disclaimer guidance in system prompt
- Append disclaimers to responses about serious issues

**Status**: implemented

## Error Handling (Completed)

Will need to handle:
- Model unavailable
- Timeout errors
- Invalid responses
- Resource exhaustion

**Current Status**: Implemented

## Next Steps for Implementation

### Immediate (Sprint 5+)

1. **Deploy Granite 1B on VM**
   - Set up model on available VM infrastructure
   - Optimize for CPU-only inference
   - Test with limited RAM constraints

## Current Limitations

**Infrastructure Constraints**:
- VM has low RAM (cannot support 3B or 8B models)
- CPU only (no GPU acceleration)
- Limited to Granite 1B model

**Model Limitations**:
- 1B model has reduced capabilities compared to larger models
- May not support advanced function calling
- Context window may be smaller
- Accuracy may be lower than 8B model (still targeting 85% per RNF-05)

**What We Don't Know Yet**:
- Actual performance on VM (inference speed)
- Real-world response quality with 1B model
- Whether 1B model meets 85% accuracy requirement (RNF-05)
- Whether responses complete within 3 seconds (RNF-01)

**What We Do Know**:
- Basic model behavior from Jupyter experiments
- Model must fit in available VM resources
- Requirements we need to meet (from Requirements.md)

## Resources and References

- IBM Granite model documentation
- Jupyter notebooks (in project repository)
- [Requirements Document](./Requirements.md) - See FR-01 to FR-06, RNF-01, RNF-05
- [System Architecture](./System-Architecture.md) - Integration points

## Summary

**Current Reality**:
- Implemented and connected to webapp
- Production code exists
- Model decided: Granite 1B (due to VM constraints)
- Integration architecture implemented
- Hosting completed

**Infrastructure Decision**:
- Granite 1B model chosen due to VM resource constraints
- VM has low RAM and CPU only (no GPU)
- Cannot upgrade to larger models (3B, 8B) with current hardware

**Next Phase**:
- Close the project


---

**Last Updated**: March 2026
**Maintained By**: IBM OBD InsightBot Team
