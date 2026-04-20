# Api Services Documentation

## 1) Clear Data Service

The `ClearDataService` is a background service that runs on a fixed schedule to automatically remove inactive user sessions and all data associated with them. This prevents old sessions from remaining in the database and ensures uploaded files are not kept indefinitely.

### Purpose
- Automatically cleans up sessions that have been inactive for more than **30 minutes**.
- Deletes all associated data:
  - chat history (`UserChatItem`)
  - uploaded OBD data (`UserOBDData`)
  - the `UserSession` record itself
  - the uploaded CSV file stored on disk

### Type
- Implements `BackgroundService`, meaning it runs continuously in the background while the application is running.

### Dependencies

- **IServiceScopeFactory**
  - Used to create a new scoped service provider inside the background worker loop.
  - Required because `ApplicationDbContext` is typically registered as a scoped dependency and cannot be injected directly as a singleton into a background service.

- **ILogger<ClearDataService>**
  - Used for logging errors during the cleanup cycle.

### Schedule / Execution Flow

- The service runs in a loop until the application shuts down (or a cancellation token is triggered).
- On each cycle:
  1. Creates a new DI scope.
  2. Resolves `ApplicationDbContext`.
  3. Calls `RemoveOldDataAsync(...)` to perform cleanup.
  4. Waits **30 minutes** before running again using `Task.Delay(...)`.

### Cleanup Logic: `RemoveOldDataAsync(ApplicationDbContext context)`

- **Cutoff time:** `DateTime.Now.AddMinutes(-30)`
- Finds all sessions where `lastUseTime` is older than the cutoff time.
- For each expired session:
  - Deletes the linked `UserOBDData` record (if present).
  - Deletes all linked `UserChatItem` messages.
  - Deletes the uploaded CSV file from disk using `UploadedDataPath` (if it exists).
- Removes the expired session records and commits changes using `SaveChangesAsync()`.

### Reliability Notes
- All cleanup runs inside a `try/catch` block so failures in one cycle do not stop the service permanently.
- File deletion is wrapped in its own `try/catch` to avoid a single filesystem error stopping database cleanup.
- Uses async EF Core methods (`ToListAsync`, `FirstOrDefaultAsync`, `SaveChangesAsync`) to avoid blocking threads during cleanup.

### Limitations / Considerations
- The inactivity threshold is fixed at 30 minutes (based on `lastUseTime`).
- Uses local server time (`DateTime.Now`). If consistent time handling is required across environments, `DateTime.UtcNow` could be considered.

## 2) Chat API Service

The `ChatbotApiService` is responsible for communicating with the external chatbot backend (Python API). It sends user messages (and optional vehicle context) to the API and returns the bot’s response as a string for the application to store/display.

### Purpose
- Encapsulates all HTTP communication with the chatbot API.
- Optionally creates/updates a chatbot session with vehicle data before sending chat messages.
- Handles failures gracefully by returning user-friendly fallback messages.

### Dependencies

- **HttpClient**
  - Used to send HTTP requests to the chatbot API endpoints.
  - Uses `PostAsJsonAsync(...)` and `ReadFromJsonAsync(...)` for JSON requests/responses.

- **ILogger<ChatbotApiService>**
  - Used for logging:
    - successful session creation
    - bot responses and performance metrics
    - warnings/errors when requests fail

### Public Methods

- **GetBotResponseAsync(string message, string sessionId, object? vehicleData)**
  - **Purpose:** Sends a chat message to the chatbot API and returns the bot’s response text.
  - **Inputs:**
    - `message`: the user’s chat message
    - `sessionId`: the C# session identifier (used to link Python and C# sessions)
    - `vehicleData`: optional vehicle context object built from stored `UserOBDData`

### Request Flow

1. **Optional session create/update**
   - If `vehicleData` is not null, the service attempts to call:
     - `POST /session/create`
   - Payload includes:
     - `session_id`
     - `vehicle_data`
   - Failures here do not stop the request; the service logs a warning and continues to chat.

2. **Send chat message**
   - Sends:
     - `POST /chat`
   - Payload includes:
     - `message`
     - `session_id`

3. **Parse response**
   - On success (`2xx` status), deserializes JSON into `ChatApiResponse`.
   - If `ChatApiResponse.Response` is present, returns it.
   - Logs intent detection and processing time where available.

### Error Handling / Reliability

The service catches common failure cases and returns a user-friendly response:

- **Unsuccessful HTTP status codes**
  - Logs status code and returns:  
    *"Sorry, I couldn't process that request. Please try again."*

- **TaskCanceledException (timeout)**
  - Returns:  
    *"Sorry, the request took too long. Please try again."*

- **HttpRequestException (connection failure)**
  - Returns:  
    *"Sorry, I'm having trouble connecting to the chatbot service. Please try again later."*

- **Unexpected exceptions**
  - Returns:  
    *"Sorry, something went wrong. Please try again."*
