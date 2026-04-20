# OBD InsightBot API

A production-ready REST API for the OBD InsightBot chatbot. This API provides natural language automotive diagnostics powered by IBM Granite 4.0-h-1b (Q3_K_S quantized).

## Features

- **Natural Language Processing**: Understands casual questions about your vehicle
- **DTC Code Explanations**: Translates error codes into plain English with caching
- **Session Management**: Maintains conversation context with automatic TTL cleanup (30-min expiration)
- **Custom Vehicle Data**: Support for different vehicles and simulated states
- **Memory Optimized**: Designed for 4GB RAM environments with proactive cleanup
- **Production Ready**: Health checks, secure CORS, logging, and error handling
- **Response Caching**: Reduces LLM calls for frequently asked DTC explanations

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone or download the API files
cd obd-insightbot-api

# Build and run
docker-compose up -d

# Check health
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How is my car doing?"}'
```

### Option 2: Python Direct

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (lightweight, no LLM)
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uvicorn app.main:app --reload
```

### Option 3: VM Deployment Script

```bash
chmod +x deploy.sh
./deploy.sh
```

## API Endpoints

### Chat

**POST /chat**

Send a message and receive a response.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What error codes do I have?",
    "session_id": "optional-session-id"
  }'
```

Response:
```json
{
  "response": "I found 2 codes. P0300 means random/multiple cylinder misfire detected...",
  "session_id": "abc123",
  "timestamp": "2024-01-15T10:30:00Z",
  "intent_detected": "explain_all_active_codes",
  "processing_time_ms": 45.2
}
```

### Session Management

**POST /session/create**

Create a new session with optional custom vehicle data.

```bash
curl -X POST http://localhost:8000/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "mark": "toyota",
    "model": "camry",
    "car_year": 2020,
    "fuel_level": 75,
    "trouble_codes": ["P0420"]
  }'
```

**GET /session/{session_id}**

Get session information.

**DELETE /session/{session_id}**

Delete a session.

**PUT /session/{session_id}/vehicle**

Update vehicle data for testing different scenarios.

### Reference

**GET /dtc-codes**

List all known DTC codes and their information.

**GET /sensors**

List available sensors and their normal ranges.

### Health

**GET /health**

Health check for monitoring and load balancers.

```json
{
  "status": "healthy",
  "model_loaded": false,
  "active_sessions": 5,
  "uptime_seconds": 3600.5,
  "version": "1.0.0"
}
```

## Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
const API_URL = 'http://your-vm-ip:8000';

interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
  intent_detected?: string;
  processing_time_ms: number;
}

class OBDInsightBot {
  private sessionId: string | null = null;

  async chat(message: string): Promise<ChatResponse> {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: this.sessionId,
      }),
    });

    const data: ChatResponse = await response.json();
    this.sessionId = data.session_id;
    return data;
  }

  async createSession(vehicleData?: object): Promise<string> {
    const response = await fetch(`${API_URL}/session/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(vehicleData || {}),
    });

    const data = await response.json();
    this.sessionId = data.session_id;
    return this.sessionId;
  }
}

// Usage
const bot = new OBDInsightBot();
const result = await bot.chat("How's my car doing?");
console.log(result.response);
```

### React Example

```tsx
import { useState, useCallback } from 'react';

const API_URL = 'http://your-vm-ip:8000';

function ChatBot() {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong.' }]);
    } finally {
      setLoading(false);
    }
  }, [input, sessionId]);

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="message assistant">Thinking...</div>}
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about your car..."
        />
        <button onClick={sendMessage} disabled={loading}>Send</button>
      </div>
    </div>
  );
}
```

## VM Deployment Guide

### Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- At least 1GB RAM (4GB recommended for LLM version)
- Python 3.11+ or Docker

### Step-by-Step Deployment

1. **SSH into your VM**
   ```bash
   ssh user@your-vm-ip
   ```

2. **Clone/upload the API files**
   ```bash
   # Option A: Git clone (if in a repo)
   git clone https://github.com/your-repo/obd-insightbot-api.git
   
   # Option B: SCP upload
   scp -r obd-insightbot-api/ user@your-vm-ip:~/
   ```

3. **Run the deployment script**
   ```bash
   cd obd-insightbot-api
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Configure firewall (if needed)**
   ```bash
   sudo ufw allow 8000/tcp  # API port
   sudo ufw allow 80/tcp    # Nginx (if using)
   ```

5. **Verify deployment**
   ```bash
   curl http://localhost:8000/health
   ```

### Production Considerations

1. **SSL/TLS**: Use Nginx with Let's Encrypt for HTTPS
2. **Domain**: Point your domain to the VM IP
3. **Monitoring**: Set up health check alerts
4. **Logging**: Configure log rotation
5. **Backups**: Regular session data backups if needed

### With LLM Support

The API uses IBM Granite 4.0-h-1b with Q3_K_S quantization for optimal memory usage:

```bash
# Use the LLM-enabled Docker image
docker-compose --profile llm up -d api-llm

# Or install full requirements
pip install -r requirements.txt
```

**LLM Configuration:**
- Model: `ibm-granite/granite-4.0-h-1b-GGUF` (Q3_K_S variant)
- Context window: 1024 tokens
- Memory usage: ~1.2GB
- Auto-downloads from HuggingFace on first run

Note: The LLM version requires 4GB RAM minimum. The model loads asynchronously during startup.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development` or `production` |
| `LOG_LEVEL` | `info` | Logging level |
| `MAX_SESSIONS` | `1000` | Maximum concurrent sessions |
| `ALLOWED_ORIGINS` | `localhost:3000,5000,5173` | Comma-separated list of allowed CORS origins |

### Security Configuration

**CORS**: By default, only localhost origins are allowed. In production, set the `ALLOWED_ORIGINS` environment variable:

```bash
export ALLOWED_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

### Memory Management

The API is optimized for 4GB RAM environments:

- **Session TTL**: Sessions expire after 30 minutes of inactivity
- **Automatic Cleanup**: Background task runs every 5 minutes to remove expired sessions
- **Max Sessions**: Limited to 1000 concurrent sessions (configurable)
- **Response Caching**: DTC explanations are cached for 1 hour (500 entries max)
- **Model**: Uses Q3_K_S quantization (~1.2GB) with 1024 token context window

## Project Structure

```
obd-insightbot-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   └── chatbot_core.py  # Core chatbot logic
├── requirements.txt      # Full dependencies (with LLM)
├── requirements-light.txt # Lightweight (no LLM)
├── Dockerfile           # Lightweight image
├── Dockerfile.llm       # Image with LLM support
├── docker-compose.yml   # Docker Compose config
├── deploy.sh            # VM deployment script
└── README.md
```

## License

MIT License - Feel free to use and modify for your projects.

## Support

For issues or questions, please open an issue on the repository.
