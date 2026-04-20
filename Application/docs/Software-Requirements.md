# Software Requirements

This document provides a high-level overview of the IBM OBD InsightBot software requirements. For detailed specifications, see the comprehensive [Requirements Document](./Requirements.md).

## Project Overview

**IBM OBD InsightBot** is a conversational AI-powered web application that translates vehicle OBD-II diagnostic data into plain-language explanations, helping users understand vehicle health without technical automotive knowledge.

**Academic Context**: Master's Course Project, University of Hull in partnership with IBM

## Functional Requirements Summary

### FR-01: General Diagnostic Feedback
Analyze uploaded OBD-II data and provide plain-language feedback about vehicle health status.

**Key Capabilities**:
- Extract and analyze key diagnostic metrics
- Identify abnormal values
- Classify issue severity (Informational/Warning/Critical)
- Provide recommended actions
- Support follow-up questions with conversation context

### FR-02: DTC Code Interpretation
Extract, lookup, and explain Diagnostic Trouble Codes (DTCs) from OBD-II data.

**Key Capabilities**:
- Extract all DTCs from uploaded files
- Provide human-readable explanations
- Classify severity levels
- Suggest appropriate user actions
- Handle unknown manufacturer-specific codes gracefully

### FR-03: Conversational Context Management
Maintain conversation history to support natural follow-up questions without requiring users to repeat information.

**Key Capabilities**:
- Maintain minimum 20 conversation exchanges
- Resolve pronouns and references (85% accuracy target)
- Recognize topic changes
- Remember uploaded data throughout session
- Clear session data on completion (privacy per RNF-03)

### FR-04: IBM Granite Function Calling
Use IBM Granite AI's function calling capabilities to invoke specific diagnostic functions based on user queries.

**Available Functions**:
- `get_quick_summary()` - Overall vehicle health status
- `explain_dtc_code(code)` - Specific DTC explanation
- `explain_all_active_codes()` - List all active DTCs
- `get_sensor_reading(sensor)` - Specific sensor value
- `get_engine_status()` - Engine health information
- `get_fuel_status()` - Fuel system information
- `get_vehicle_info()` - Vehicle make/model/year

### FR-05: Data Upload and Parsing
Allow users to upload OBD-II diagnostic log files (CSV/JSON) and parse them for analysis.

**Key Capabilities**:
- Support CSV and JSON formats
- Drag-and-drop and file browser upload
- File validation before processing
- Parse within 5 seconds for files up to 5MB
- Reject files exceeding 5MB limit
- Provide helpful error messages for malformed files

### FR-06: Session History
Display conversation history within diagnostic sessions.

**Key Capabilities**:
- Store all user queries and AI responses
- Display in chronological order
- Support pagination for long conversations
- Include function call information
- Clear history when session ends

## Non-Functional Requirements Summary

### RNF-01: Response Time
**Requirement**: 90% of AI queries must complete within 3 seconds
**Priority**: High
**Rationale**: Maintain conversational flow and user engagement

### RNF-02: Safety and Liability Disclaimers
**Requirement**: Display prominent disclaimers that the system is not a replacement for professional inspection
**Priority**: Critical
**Rationale**: Legal liability protection, user safety

### RNF-03: Data Privacy & Session Management
**Requirement**: No persistent storage of user data; session-based only
**Priority**: High
**Rationale**: Privacy protection, GDPR consideration

**Details**:
- Data stored only during active session
- Session expires after inactivity
- All data deleted on session end
- No user accounts or authentication

### RNF-04: Conversation Scope Control
**Requirement**: System should politely decline off-topic queries and guide users back to automotive diagnostics
**Priority**: Medium
**Rationale**: Maintain focus on core functionality, prevent misuse

### RNF-05: Natural Language Understanding
**Requirement**: 85% intent detection accuracy for automotive diagnostic queries
**Priority**: High
**Rationale**: Ensure useful and accurate responses

**Measurement**: Manual review of sample queries and responses

### RNF-06: Code Quality & Testing
**Requirement**: Minimum 70% code coverage with automated tests
**Priority**: High
**Rationale**: Ensure code quality, reduce bugs, facilitate maintenance

**Details**:
- Unit tests for business logic
- Integration tests for API endpoints
- CI/CD pipeline integration
- Coverage reports on pull requests

### RNF-07: Browser Compatibility
**Requirement**: Support latest 2 versions of Chrome, Firefox, Safari, and Edge
**Priority**: Medium
**Rationale**: Maximize user accessibility

**Testing**: Manual cross-browser testing

### RNF-08: Language Support
**Requirement**: English language only for initial version
**Priority**: Low (for expansion)
**Rationale**: Scope management for academic project

### RNF-09: IBM Granite Dependency
**Requirement**: System must use IBM Granite as the AI model
**Priority**: High (Project Requirement)
**Rationale**: IBM partnership requirement

## User Classes and Characteristics

| User Class | Description | Technical Knowledge | Primary Goal |
|------------|-------------|---------------------|--------------|
| **Vehicle Owner** | Primary target user | Low to Medium | Understand vehicle diagnostics without technical jargon |
| **Hobbyist Mechanic** | User with some automotive knowledge | Medium | Get detailed DTC explanations and diagnostic insights |
| **Administrator** | System maintainer | High | Manage system, monitor performance, troubleshoot issues |

## System Constraints

1. **No Live Vehicle Data**: System uses pre-recorded OBD-II logs only (provided by IBM)
2. **IBM Granite Required**: Must use IBM Granite AI (project requirement)
3. **English Only**: Single language support initially
4. **Academic Budget**: Limited resources for infrastructure
5. **Browser-Based**: No native mobile applications initially
6. **Internet Required**: Online connectivity needed for AI processing

## Dependencies

| Dependency | Version | Purpose | Criticality |
|------------|---------|---------|-------------|
| **.NET SDK** | 8.0+ | Backend and frontend framework | Critical |
| **IBM Granite AI** | 3.0/4.0 8B Instruct | Conversational AI engine | Critical |
| **SQL Server** | 2019+ | Session data storage | High |
| **Blazor WASM** | .NET 8.0 | Frontend framework | Critical |
| **MudBlazor** | Latest | UI component library | High |
| **Entity Framework Core** | 8.0+ | Data access layer | High |
| **SignalR** | .NET 8.0 | Real-time communication | Medium |

## System Features Priority

| Priority | Features |
|----------|----------|
| **P1 - Critical** | FR-01 (Diagnostic Feedback), FR-02 (DTC Interpretation), FR-05 (Data Upload), RNF-02 (Safety Disclaimers), RNF-09 (IBM Granite) |
| **P2 - High** | FR-03 (Context Management), RNF-01 (Response Time), RNF-03 (Data Privacy), RNF-05 (NLU Accuracy), RNF-06 (Code Quality) |
| **P3 - Medium** | FR-04 (Function Calling), FR-06 (Session History), RNF-04 (Scope Control), RNF-07 (Browser Compatibility) |
| **P4 - Low** | Suggested questions, UI enhancements, RNF-08 (Multi-language) |

## Requirements Traceability

| User Story | Functional Requirement | Implementation Status |
|------------|------------------------|----------------------|
| US 1.1 - Upload OBD-II Logs | FR-05 | Planned |
| US 1.2 - AI Analyzes Data | FR-01 | Planned |
| US 1.3 - Answer Diagnostic Questions | FR-03 | Planned |
| US 1.4 - Explain Fault Codes | FR-02 | Planned |
| US 1.6 - View Past Q&A | FR-06 | Planned |
| US 1.7 - Handle Off-topic Questions | RNF-04 | Planned |
| US 2.2 - Legal Notices | RNF-02 | Implemented (Documentation) |
| US 2.7 - Managing User Data | RNF-03 | Planned |

See [User Stories Document](./User-Stories.md) for complete user story details.

## Acceptance Criteria Overview

Each requirement includes specific, testable acceptance criteria. Examples:

**FR-01 (Diagnostic Feedback)**:
- ✓ System extracts key metrics from OBD-II data
- ✓ System identifies abnormal values
- ✓ Responses delivered in plain language
- ✓ Severity classification provided
- ✓ Recommended actions included

**RNF-01 (Response Time)**:
- ✓ 90% of queries complete within 3 seconds
- ✓ Measured and tracked via application telemetry
- ✓ Response times logged for analysis

**RNF-06 (Code Coverage)**:
- ✓ Minimum 70% code coverage
- ✓ Automated test execution in CI/CD
- ✓ Coverage reports on pull requests

## Requirements Changes

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Oct 2025 | Initial requirements | Team |
| 1.1 | Nov 2025 | Added function calling details | Team |
| 1.2 | Dec 2025 | Refined NFRs, added traceability matrix | Team |

## Next Steps for Implementation

1. **Phase 1 - Foundation**:
   - Set up project structure (.NET solution)
   - Implement session management (FR-06, RNF-03)
   - Create database schema

2. **Phase 2 - Core Features**:
   - Implement OBD-II file upload and parsing (FR-05)
   - Integrate IBM Granite AI (FR-04, RNF-09)
   - Build conversational interface (FR-03)

3. **Phase 3 - Diagnostic Features**:
   - Implement DTC lookup and explanation (FR-02)
   - Build diagnostic analysis (FR-01)
   - Add session history display (FR-06)

4. **Phase 4 - Polish**:
   - Implement safety disclaimers (RNF-02)
   - Optimize response times (RNF-01)
   - Browser compatibility testing (RNF-07)
   - Achieve 70% code coverage (RNF-06)

## MoSCoW Prioritization

### Must Have
- OBD-II file upload and parsing
- DTC code explanation
- Conversational AI integration with IBM Granite
- Safety and liability disclaimers
- Session-based data management (no persistence)
- 70% code coverage

### Should Have
- Conversation context management (20+ exchanges)
- Function calling capabilities
- Session history display
- 90% queries under 3 seconds
- Cross-browser compatibility

### Could Have
- Suggested questions for new users
- Advanced diagnostic insights
- Performance monitoring dashboard

### Won't Have (This Version)
- Multi-language support
- User authentication/accounts
- Historical trend analysis
- Mobile native applications
- Live vehicle data connection

## Related Documentation

- **[Requirements (Detailed SRS)](./Requirements.md)** - Complete software requirements specification with detailed criteria
- **[User Stories](./User-Stories.md)** - Product backlog with epics and user stories
- **[System Architecture](./System-Architecture.md)** - Technical architecture and design decisions
- **[API Documentation](./API-Documentation.md)** - REST API endpoint specifications
- **[Testing Strategy](./Testing-Strategy.md)** - Testing approach and quality assurance

---

**Last Updated**: January 2026
**Maintained By**: IBM OBD InsightBot Team
