# Chat View Documentation (Razor / HTML)

**File:** *(Chat view Razor page – e.g., `LetsChat.cshtml`)*  
**Model:** `UserSession`  
**Layout:** `_ChatLayout`

This Razor view renders the main chat interface. It displays existing chat messages for a session, provides a message input form, and includes UI elements such as upload context, a dropdown menu, and a “thinking” indicator.

---

### Purpose
- Display the conversation history for the current `UserSession`.
- Provide an input box for users to send new messages to the chatbot.
- Show basic context about uploaded vehicle data.
- Provide menu actions for starting a new chat, uploading CSV data, and clearing stored data.

---

### Data Used (Model + ViewBag)

- **Model:** `UserSession`
  - Uses `@Model.Id` as the active `SessionID` when submitting new messages and when clearing data.

- **ViewBag.UsersChats** (`List<UserChatItem>`)
  - Chat history used to render messages in order.
  - If null, defaults to an empty list.

- **ViewBag.UploadedFileCount** (`int`)
  - Used to display the “context banner” showing how many files have been uploaded.
  - If null, defaults to `0`.

---

### Main UI Sections

#### 1) Context Banner
- Shown only when `uploadedFileCount > 0`.
- Displays a small banner with a vehicle icon and the number of uploaded files.

#### 2) Chat Messages Panel
- Displays all messages inside `.chat-messages`.
- If there are no messages, shows a default greeting: *“How may I assist you today?”*
- Includes a hidden “thinking indicator” row (`#thinkingIndicator`) that is shown while the user’s message is being submitted.

#### 3) Message Rendering Rules
The view loops through `userChats` and displays messages depending on `chat.ItemBy`:

- **System messages (`ChatSender.System`)**
  - Rendered as centered muted text (not a bubble).

- **User messages (`ChatSender.User`)**
  - Rendered right-aligned using `.user-row` and `.user-bubble`.

- **Bot messages (default case)**
  - Rendered left-aligned with a bot avatar and `.bot-bubble`.

---

### Message Input Form

The form submits a new chat message to the controller:

- **Form target:**
  - `asp-controller="Chat"`
  - `asp-action="newChatMessage"`
  - `method="post"`

- **Inputs:**
  - Hidden input: `SessionID = @Model.Id`
  - Text input: `message` (required)

- **Submit button:**
  - Shows a send icon by default.
  - Switches to a spinner and disables the button once the form is submitted.

---

### Dropdown Menu Actions

The menu provides quick navigation actions:

- **New Chat**
  - Links to `Chat/NewChat` *(controller action must exist for this to work)*

- **Upload CSV**
  - Links to `Chat/Upload` *(controller action must exist for this to work)*

- **Clear Data**
  - Calls `Chat/RemoveMyData` with `SessionID`

- **Clear Chat**
  - Currently also calls `Chat/RemoveMyData` with `SessionID`
  - **Note:** This duplicates “Clear Data” behaviour. If the intention is to clear chat only, it should call a separate endpoint (e.g., `ClearChat`) that deletes `UserChatItem` but keeps the session/OBD data.

---

### Disclaimer
A disclaimer is displayed below the input area:

> “This application should not be relied upon, always seek professional advice.”

---

### Styling (Embedded CSS)
The page contains embedded CSS defining:

- Layout structure (`.chat-container`, `.chat-messages`)
- Bot/user bubble styles (`.bot-bubble`, `.user-bubble`)
- Input area styling (`.input-container`, `.chat-input`)
- Dropdown menu styling
- “Thinking…” animation using `@keyframes blink`
- Light theme overrides via `[data-theme="light"]`

---

### Client-side Behaviour (Embedded JavaScript)

On form submission, the script:
1. Disables the send button.
2. Replaces the send icon with a loading spinner.
3. Immediately appends the user’s message to the chat UI (optimistic UI update).
4. Shows the “thinking indicator”.
5. Scrolls the chat panel to the bottom.
