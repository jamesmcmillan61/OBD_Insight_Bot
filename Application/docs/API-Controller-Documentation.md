#Controller Documentation

## 1) Controllers (Overview)

Purpose: Controllers handle routing and request/response flow in the MVC application. They receive HTTP requests, call services/database logic where needed, and return Views (or redirects) to the client.

### Controllers in this project:

* ChatController → main chatbot flow + CSV upload + session lifecycle 

* HomeController → landing page + DB connectivity check 

* Help → help/info pages 

* SettingsController → settings page entry point 

### Shared Dependencies

Across the controllers, the following shared dependencies/patterns are used:

* ApplicationDbContext: Used to access the database and persist/retrieve application data such as sessions, chat messages, and uploaded OBD data. Used in: ChatController, HomeController

* ASP.NET Core MVC Framework (Controller): All controllers inherit from Controller and return MVC Views using View() and redirects using RedirectToAction().

* ViewBag: Used to pass temporary dynamic data from controllers into Views (e.g., session IDs, chat history, DB connectivity status).

* Services (Dependency Injection): Controllers receive services via constructor injection. Example: ChatController injects ChatbotApiService to communicate with the chatbot backend.

* Logging: HomeController uses ILogger<HomeController> for standard application logging.

## 2) ChatController: file name: ChatController.cs

### 2.1 Responsibilities

The ChatController is the core controller responsible for managing the full chatbot user journey, from starting a session to uploading vehicle data and holding a conversation with the bot. It acts as the main orchestration layer between the MVC Views, the database, and the chatbot API service.

Its responsibilities include:

* Managing user sessions (UserSession)

* Creates a new user session when the user agrees to the Terms of Use.

* Tracks session activity using timestamps such as SessionStartTime and lastUseTime.

* Uses the session ID (SessionID) as the key identifier to link user data and chat history together.

* Handling the Terms of Use flow

* Provides endpoints for displaying the Terms of Use page.

* Supports both “Agreed” and “Disagreed” user flows.

* When a user agrees, the controller generates and stores a new session in the database and passes the session into the next view so the user can continue into the application.

* Uploading and parsing CSV data into UserOBDData

* Allows users to upload their vehicle data as a CSV file.

* Performs validation checks such as: ensuring a session is selected, ensuring a file is provided, enforcing CSV file type restrictions, limiting file size. 

* Saves the uploaded file to the server and stores the file path in the session record.

* Extracts relevant fields from the CSV and maps them into a UserOBDData database record tied to the session.

* Storing chat history (UserChatItem)

* Saves every user message and bot response into the database.

* Maintains ordering using ChatPosition so conversations are displayed in the correct sequence.

* Creates a default “welcome” system message when a new chat session contains no prior messages.

* Calling ChatbotApiService to generate bot replies

* Sends the user’s message and associated vehicle/OBD session data to the chatbot API service.

* Converts stored OBD data into a structured format expected by the chatbot backend (including type conversions such as int and double where possible).

* Stores the bot’s response back into the chat history.

* Provides a fallback response if the chatbot service cannot be reached or errors occur.
### 2.2 Dependencies

The ChatController uses dependency injection to access the database layer and the chatbot integration service.

ApplicationDbContext _context: Entity Framework Core database context used to read/write application data.

Used for: creating and updating UserSession records, storing and retrieving UserChatItem messages, storing and retrieving parsed UserOBDData, session cleanup/data deletion operations.

ChatbotApiService _chatbotApi: Service responsible for communicating with the external chatbot backend (Python API).

Used to generate bot responses by sending: the user’s message, the session identifier, parsed vehicle/OBD context data.

### 2.3 Endpoints (Routes + Purpose)

* **GET /TermsOfUse**: Displays Terms of Use page. Method: Index()

* **GET /TermsOfUse/Disagreed:** User disagrees with terms. Method: TandCDisagree()

* **GET /TermsOfUse/Agreed** Creates a new UserSession. Stores it in DB and passes session into view. Method: TandCAgree()

* **POST UploadFile** Uploads a CSV file for the selected session. Validates: Session exists. File exists and is not empty. File extension is .csv. File size max 10MB. 
Saves file under wwwroot/uploads using GUID filename. Extracts relevant fields and saves into UserOBDData. Redirects to chat page on success
Method: UploadFile(Guid SessionID, IFormFile file)

* **GET Chat/** Loads chat page for a session. Fetches: UserSession. Chat history ordered by ChatPosition. UserOBDData for session. Creates a default welcome message if no chat exists.
Method: LetsChat(Guid SessionID)

* **POST newChatMessage** Validates user input message (non-empty, trimmed, max length 1000). Stores user message in DB. Updates session lastUseTime. Calls bot response handler. Redirects back to chat view
Method: newChatMessage(Guid SessionID, string message)

### 2.4 Core Internal Logic

The ChatController contains internal helper methods that support the main endpoints by handling CSV parsing and chatbot integration.

* **ExtractRelevantDataFromFile(Guid SessionID, string filePath)**

  - Purpose: Parses the uploaded CSV file and stores a structured UserOBDData record linked to the current session.

  - Behaviour: Verifies the file exists on disk before processing. Reads all lines from the CSV file and ensures there is enough data (requires at least header row + one value row).

  - Treats: Row 1 as headers, Row 2 as the corresponding values. Validates that header and value counts match. Creates a new UserOBDData entity and assigns: UserSessionId = SessionID
  
  - Returns: true when parsing + save succeeds, otherwise false. 
 
* **ResponceFromBot(Guid SessionID, string userMessage)**

  - Purpose: Generates a chatbot response for the user message using stored vehicle context data.

  - Behaviour: Loads the session’s UserOBDData record from the database (if available). Builds a vehicleData object in the format expected by the chatbot API, including:
   vehicle identifiers such as mark, model, parsed numeric fields where possible (car_year, engine_rpm, speed, fuel_level, etc.), a list of trouble codes split from the stored comma-separated string.
 
  - Calls the chatbot integration layer: _chatbotApi.GetBotResponseAsync(userMessage, SessionID.ToString(), vehicleData) Stores the bot response as a UserChatItem with sender type Bot.

  - Failure handling: If an exception occurs (e.g., API connection issue), the controller: logs the error to debug output,
   stores a fallback bot message: “Sorry, I'm having trouble connecting to the chatbot service. Please try again.”

### 2.5 Data Deletion / Cleanup

The `ChatController` includes methods for deleting user data and cleaning up inactive sessions to prevent unnecessary storage usage and ensure user privacy.

- **RemoveMyData(Guid SessionID)**
  - **Purpose:** Allows the user to delete all data linked to their current session.
  - **Deletes:**
    - all chat history (`UserChatItem`) linked to the session
    - uploaded OBD data (`UserOBDData`) linked to the session
    - the `UserSession` record itself
    - the uploaded CSV file from disk (if it exists)
  - **Notes:**
    - Uses safety checks to ensure the session exists before attempting deletion.
    - Removes the uploaded file using the path stored in `UserSession.UploadedDataPath`.

- **RemoveOldData()**
  - **Purpose:** Removes inactive sessions and their related data to keep the database clean and reduce stored files.
  - **Behaviour:**
    - Finds sessions where `lastUseTime` is older than 30 minutes.
    - For each inactive session, deletes:
      - associated `UserOBDData` (if present)
      - associated `UserChatItem` records
      - the uploaded CSV file from disk (if it exists)
    - Removes expired sessions from the database.

---

### 2.6 Security / Reliability Notes

The `ChatController` includes several security and reliability improvements to protect user data and improve performance:

- **File upload hardening:** Uploaded files are saved using GUID-based filenames rather than user-provided filenames, reducing the risk of path traversal attacks.
- **File type restriction:** Only `.csv` files are accepted to prevent unsupported or unsafe file uploads.
- **File size limit:** Upload size is limited (10MB max) to reduce the risk of abuse and oversized uploads.
- **Async DB operations:** Uses asynchronous Entity Framework methods in key chat flows to avoid blocking threads and improve scalability.
- **Input validation:** User chat messages are validated (non-empty, trimmed, and limited to 1000 characters) to prevent abuse and ensure consistent storage.

---

## 3) HomeController Documentation  
**File:** `HomeController.cs`

### 3.1 Responsibility

The `HomeController` is responsible for serving the main landing pages of the application and performing a basic database connectivity check to confirm the backend is available.

### 3.2 Endpoints (Routes + Purpose)

* **GET /**: Loads the home page and checks database connectivity using `_context.Database.CanConnect()`. Stores the result in `ViewBag.dbConnected`. **Method:** `Index()`
* **GET /Home/Privacy**: Displays the Privacy page. **Method:** `Privacy()`
* **GET /Home/Error**: Returns an error page containing the request ID for debugging. **Method:** `Error()`

---

## 4) Help Controller Documentation  
**File:** `Help.cs`

### 4.1 Responsibility

The `Help` controller serves static help and support pages for the application.

### 4.2 Endpoints (Routes + Purpose)

* **GET /Help/Index**: Displays the main Help page. **Method:** `Index()`
* **GET /Help/Example**: Displays an example help page. **Method:** `Example()`

---

## 5) SettingsController Documentation  
**File:** `SettingsController.cs`

### 5.1 Responsibility

The `SettingsController` provides access to the settings view of the application.

### 5.2 Endpoints (Routes + Purpose)

* **GET /Settings/Index**: Displays the Settings page. **Method:** `Index()`