# System Architecture

This document describes the high-level system architecture, component design, and technical decisions for the IBM OBD InsightBot project.

**Status**: Design Phase - Architecture is completed
- Code implementation exists
- API endpoints created
- database schema implemented
- This document serves as the architectural design specification for future implementation

## Architecture Overview

IBM OBD InsightBot will follow a **three-tier client-server architecture** with clear separation of concerns:

1. **Presentation Layer**: Blazor WebAssembly (frontend) - Completed
2. **Application Layer**: FastAPI Api (backend) - Completed
3. **Data Layer**: SQL Server (session data) + IBM Granite AI (external service) - Completed

## Architecture Philosophy

Our architectural decisions are guided by:

- **Separation of Concerns**: Each layer has distinct responsibilities
- **Scalability**: Design supports future horizontal scaling
- **Maintainability**: Clear boundaries enable independent component development
- **Testability**: Loose coupling through dependency injection
- **Security**: No persistent user data (session-based per RNF-03)

## High-Level Architecture Diagram (Design)

**Note**: This is the planned architecture. 

```
┌─────────────────────────────────────────────────────────────┐
│                 Client (Browser) - COMPLETED                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │      Blazor WebAssembly Application - BUILT            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │ │
│  │  │  MudBlazor   │  │   Pages &    │  │   Services   │  │ │
│  │  │  Components  │  │  Components  │  │  (State Mgmt)│  │ │
│  │  │   (REMOVED)  │  │ (COMPLETED)  │  │   (COMPLETED)│  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS / SignalR 
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            FastApi  API - COMPLETED                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │             API Controllers - COMPLETED                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │ │
│  │  │ Session  │  │   Chat   │  │Diagnostic│              │ │
│  │  (COMPLETED)│  (COMPLETED)│  (COMPLETED)│              │ │
│  │  └──────────┘  └──────────┘  └──────────┘              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Business Logic Layer -COMPLETED               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │ │
│  │  │ OBD Parser   │  │  Diagnostic  │  │    Chat     │   │ │
│  │  │(COMPLETED)   │  │   (COMPLETED)│  │  (COMPLETED)│   │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │ │
│  │  │  IBM Granite │  │     DTC      │  │   Session   │   │ │
│  │  │(COMPLETED)   │  │ (COMPLETED)  │  │  (COMPLETED)│   │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Data Access Layer - COMPLETED                 │ │
│  │  ┌──────────────┐  ┌──────────────┐                    │ │
│  │  │   EF Core    │  │  Repository  │                    │ │
│  │  │  (COMPLETED) │  │ (COMPLETED)  │                    │ │
│  │  └──────────────┘  └──────────────┘                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐
│   SQL Server DB      │         │  IBM Granite 1B      │
│  (COMPLETED)         │         │ (Jupyter notebooks   │
│                      │         │  COMPLETED)          │
└──────────────────────┘         └──────────────────────┘
```

## Component Breakdown (Planned Design)

**Important**: All components described below are implemented. 

### 1. Presentation Layer (Frontend) - Completed

**Technology**: ASP .NET frontend

**Planned Responsibilities**:
- Render user interface
- Handle user interactions
- Manage client-side state
- Communicate with backend API
- Display real-time chat updates via SignalR

**Planned Key Components**:

#### Pages (COMPLETED)
- **Home Page**: Landing page with project overview
- **Upload Page**: OBD-II file upload interface (FR-05)
- **Chat Page**: Conversational interface with AI
- **History Page**: Session history display (FR-06)

**Current Status**: COMPLETED

#### MudBlazor Components (REMOVED)
- **MudFileUpload**: Drag-and-drop file upload
- **MudDialog**: Confirmation dialogs and alerts
- **MudDataGrid**: Display session history
- **MudCard**: Container for diagnostic information
- **MudChip**: Display DTC codes with severity colors
- **MudTextField**: User query input

**Current Status**: REMOVED

#### Services (Client-Side) - COMPLETED
- **SessionStateService**: Manage current session state
- **ApiClient**: HTTP client for API communication
- **SignalRClient**: Real-time connection to chat hub

**Current Status**: No client-side services exist yet

#### State Management (COMPLETED)
- Session ID and uploaded data status
- Current conversation history
- Loading states and error messages

**Communication** (COMPLETED)
- Fast APi connects frontend to backend

**Current Status**: No API communication layer implemented

### 2. Application Layer (Backend) - COMPLETED

**Technology**: ASP.NET Core 8.0 (COMPLETED)

**Planned Responsibilities**:
- Process business logic
- Integrate with IBM Granite AI
- Parse OBD-II files
- Manage sessions
- Handle real-time chat communication


**Current Status**: API controllers implemented.

#### API Controllers (COMPLETED)

**SessionController** (COMPLETED):
- `POST /api/session/create` - Create new diagnostic session
- `GET /api/session/{id}` - Get session details
- `DELETE /api/session/{id}` - Clear session data
- `POST /api/session/{id}/upload` - Upload OBD-II file

**ChatController** (COMPLETED):
- `POST /api/chat/query` - Send user query to AI
- `GET /api/chat/history/{sessionId}` - Retrieve conversation history

**DiagnosticsController** (COMPLETED):
- `POST /api/diagnostics/analyze` - Trigger full diagnostic analysis
- `GET /api/diagnostics/dtc/{code}` - Get specific DTC explanation
- `GET /api/diagnostics/summary/{sessionId}` - Get diagnostic summary

**Current Status**: Controllers exist and are implemented. 

#### Business Logic Services (COMPLETED)

**OBDParserService** (COMPLETED):
- Parse CSV/JSON OBD-II files (FR-05)
- Extract DTCs and sensor readings
- Validate file format and content
- Convert to internal data model

**DiagnosticService** (COMPLETED):
- Analyze parsed OBD-II data (FR-01)
- Identify abnormal sensor readings
- Classify issue severity
- Generate diagnostic summary

**DTCLookupService** (COMPLETED):
- Look up DTC codes in database/reference data (FR-02)
- Return standardized DTC descriptions
- Provide severity classification
- Suggest user actions

**GraniteAIService** (COMPLETED):
- Integrate with self-hosted IBM Granite 1B model
- Handle function calling if supported (FR-04)
- Manage conversation context (FR-03)
- Parse AI responses
- Implement retry logic and error handling

**Note**:C# integration service exists see [IBM-Granite-Integration.md](./IBM-Granite-Integration.md) for current status.

**ChatService** (COMPLETED):
- Orchestrate chat interactions
- Maintain conversation history (FR-03)
- Route queries to appropriate services
- Format responses for frontend

**SessionManager** (COMPLETED):
- Create and manage diagnostic sessions
- Store session data in memory/database
- Implement session timeout (per RNF-03)
- Clear session data on completion

**Current Status**: Service classes implemented.

#### Data Access Layer (COMPLETED)

**Entity Framework Core** (COMPLETED):
- ORM for database operations
- Code-first migrations
- Connection pooling

**DbContext** (COMPLETED):
- `OBDInsightBotDbContext` - Main database context

**Entities** (COMPLETED):
- `Session` - Diagnostic session data
- `ConversationHistory` - Chat messages
- `UploadedFile` - File metadata
- `DiagnosticResult` - Analysis results

**Repository Pattern** (Optional, COMPLETED):
- `ISessionRepository` - Session data operations
- `IConversationRepository` - Chat history operations

**Current Status**: Database models, DbContext, Repositories exist.

### 3. Data Layer - COMPLETED

#### SQL Server Database (COMPLETED)

**Purpose**: Temporary session data storage (in-memory or short-lived)

**Planned Schema**:

**Note**: Database exists. This is the planned schema design.

```sql
-- Sessions Table (COMPLETED)
CREATE TABLE Sessions (
    SessionId UNIQUEIDENTIFIER PRIMARY KEY,
    CreatedAt DATETIME2 NOT NULL,
    ExpiresAt DATETIME2 NOT NULL,
    VehicleData NVARCHAR(MAX),  -- JSON serialized OBD-II data
    Status NVARCHAR(50)
);

-- ConversationHistory Table (COMPLETED)
CREATE TABLE ConversationHistory (
    MessageId INT IDENTITY(1,1) PRIMARY KEY,
    SessionId UNIQUEIDENTIFIER FOREIGN KEY REFERENCES Sessions(SessionId),
    Role NVARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    Content NVARCHAR(MAX) NOT NULL,
    Timestamp DATETIME2 NOT NULL,
    FunctionCalled NVARCHAR(100)
);

-- DiagnosticResults Table (COMPLETED)
CREATE TABLE DiagnosticResults (
    ResultId INT IDENTITY(1,1) PRIMARY KEY,
    SessionId UNIQUEIDENTIFIER FOREIGN KEY REFERENCES Sessions(SessionId),
    DtcCode NVARCHAR(10),
    Severity NVARCHAR(20),
    Description NVARCHAR(MAX),
    CreatedAt DATETIME2 NOT NULL
);
```

**Current Status**: Database configured. Tables created. This is planned schema design.

**Planned Data Retention**:
- Sessions expire after inactivity (e.g., 1 hour)
- Automated cleanup job removes expired sessions
- No persistent user data per RNF-03

#### IBM Granite AI Integration

**Current Status**: IBM Granite model exists and implemented

**Planned Integration**:
- Self-hosted Granite 1B model (VM constraints: low RAM, CPU only)
- Not using Watson API or cloud-hosted model
- Will need to build C# integration service (does not exist yet)

**Current Reality**:
- See [IBM-Granite-Integration.md](./IBM-Granite-Integration.md) for detailed current status

## Integration Points (COMPLETED)

**Important**: Integration code exists. These are the planned integration approaches.

### 1. Frontend-Backend Communication (COMPLETED)

**Planned Protocol**: FastAPI Api

**FastAPI** (COMPLETED):
- File upload (multipart/form-data)
- JSON request/response bodies

**Authentication** (COMPLETED): Session-based (session ID in requests)

**Current Status**: API endpoints exist. 

### 2. Backend-IBM Granite AI Integration (COMPLETED)

**Current Status**: Completed

**Planned Approach**:
- Self-hosted Granite 1B model (VM resource constraints)
- C# service to communicate with hosted model
- Integration method to be determined during implementation

**What Doesn't Exist**:
- No hosting infrastructure configured

### 3. OBD-II Data Processing (COMPLETED)

**Planned Input Formats** (FR-05):
- CSV: Comma-separated values
- JSON: Structured diagnostic data

**Planned Processing Flow**:
1. User uploads file via frontend
2. Backend validates file size (< 5MB) and format
3. OBDParserService parses file content
4. Data stored in session context
5. DiagnosticService analyzes data
6. Results displayed in chat interface

**Current Status**: OBDParserService exists. File upload handling implemented.

## Data Flow (COMPLETED)

**Note**: These are planned data flows. 

### User Query Flow (COMPLETED)

**Planned Flow**:
```
1. User enters question in chat interface
2. Frontend sends POST request to /api/chat/query
3. ChatService receives query
4. SessionManager retrieves session context
5. GraniteAIService sends query to IBM Granite
6. Granite AI processes query (may call functions)
7. ChatService formats response
8. Response returned to frontend
9. Frontend displays response in chat
10. Conversation history updated (FR-03)
```

**Current Status**: Chat interface exists. API endpoints created. AI integration service implemented.

### File Upload Flow (COMPLETED)

**Planned Flow**:
```
1. User uploads OBD-II file (CSV/JSON)
2. Frontend sends POST to /api/session/{id}/upload
3. Backend validates file format and size
4. OBDParserService parses file content
5. DTCs extracted and stored in session
6. DiagnosticService performs initial analysis
7. Summary returned to frontend
8. User can now ask questions about data
```

**Current Status**: Upload interface exists. Parser service implemented. Session management created.

## Security Considerations (COMPLETED)

**Note**: These are planned security measures. 

### Data Privacy (RNF-03) - COMPLETED

Planned security measures:
- **No Persistent Storage**: Session data deleted after expiration
- **Session Isolation**: Each session has unique ID, no cross-session access
- **Secure Transmission**: All data sent over HTTPS
- **API Key Protection**: Configuration secrets managed securely

**Current Status**: COMPLETED

### Input Validation (COMPLETED)

Planned validation:
- File size limits (5MB per FR-05)
- File format validation (CSV/JSON only)
- SQL injection prevention (Entity Framework parameterized queries)
- XSS prevention (Blazor automatic encoding)

**Current Status**: COMPLETED

### Safety Disclaimers (RNF-02) - COMPLETED

Planned disclaimers:
- Prominent disclaimer on all diagnostic pages
- Clear messaging that system is not a replacement for professional inspection
- Liability disclaimers in legal notices

**Current Status**: Legal notices exist in [LegalNotices.md](./LegalNotices.md), UI implementation complete.

## Technology Decisions Rationale

### Why Blazor WebAssembly?

- **C# Full-Stack**: Single language for frontend and backend
- **Type Safety**: Compile-time type checking
- **Code Sharing**: Share DTOs and models between layers
- **Performance**: Client-side execution reduces server load
- **Modern**: Supports latest web standards

### Why ASP.NET Core?

- **High Performance**: Excellent throughput and latency
- **Cross-Platform**: Runs on Windows, Linux, macOS
- **Built-in DI**: Dependency injection out of the box
- **SignalR**: Real-time communication support
- **Ecosystem**: Rich library support

### Why SQL Server?

- **Reliability**: Enterprise-grade database
- **Integration**: Excellent EF Core support
- **Development**: LocalDB for easy local development
- **Familiarity**: Team expertise with SQL Server

### Why IBM Granite AI?

- **Project Requirement**: Specified by IBM partnership
- **Model Choice**: Using Granite 1B due to VM constraints (low RAM, CPU only)
- **Self-Hosted**: Will host model ourselves (not using Watson API)
- **Current Status**: Experimenting in Jupyter notebooks only

## Scalability Considerations (Future Planning)

**Note**: These are future considerations. Current focus is on single-instance prototype.

### Horizontal Scaling (Future)

Potential approaches:
- **Stateless API**: Session data in database, not memory
- **Load Balancer**: Distribute requests across multiple API instances
- **Database Scaling**: Read replicas for session queries

**Current Status**: Complete

### Performance Optimization (Planned)

Planned optimizations:
- **Caching**: Cache DTC lookup results (reduce database queries)
- **Connection Pooling**: Reuse database connections
- **Async/Await**: Non-blocking I/O operations
- **Response Compression**: Reduce payload size

**Current Status**: Performance optimization will be addressed during implementation phase.

### Monitoring (Complete)

Planned monitoring:
- Application telemetry
- Logging infrastructure
- Health check endpoints
- Performance metrics dashboard

**Current Status**: Metrics can be viewed

## Deployment Architecture (Complete)

- See [Deployment-Guide.md](./Deployment-Guide.md) for detailed deployment plans.

### Planned Hosting

Planned hosting approach:
- **Frontend**: Static Web App (Blazor WASM)
- **Backend**: App Service (ASP.NET Core)
- **Database**: SQL Server (configuration TBD)
- **Configuration**: Secure secrets management

**Current Status**: WebApp and AI are deployed to the VM

### CI/CD Pipeline (Complete)

Planned CI/CD:
- Azure DevOps pipelines
- Automated testing on commit
- Staged deployments (dev → staging → production)

- See [Deployment-Guide.md](./Deployment-Guide.md).

## Future Enhancements

1. **Real-time Collaboration**: Multiple users analyzing same vehicle data
2. **Historical Analytics**: Track diagnostic trends over time
3. **Mobile App**: Native iOS/Android applications
4. **Offline Mode**: Cache diagnostic data for offline analysis
5. **Multi-Language Support**: Extend beyond English (RNF-08)

## Summary

**Current Reality**:
- This document describes the **planned architecture only**
- No deployment infrastructure

**What Exists Now**:
- Architecture design and planning documentation
- Requirements specification ([Requirements.md](./Requirements.md))
- Jupyter notebook experiments with IBM Granite 1B model
- Documentation and planning phase (Sprint 5)
- API endpoints created
- Database configured
- Frontend pages built
- Continue and finalize deployment

## Additional Resources

- [Blazor Architecture](https://learn.microsoft.com/en-us/aspnet/core/blazor/)
- [ASP.NET Core Architecture](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/)
- [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core/)
- [IBM Granite Documentation](https://www.ibm.com/products/watsonx-ai)

---

**Last Updated**: March 2026
**Maintained By**: IBM OBD InsightBot Team
