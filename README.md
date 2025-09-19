# Hotel Booking Chatbot - Flask + SQLite + spaCy

A complete single-page application (SPA) for hotel bookings using Flask backend, SQLite database, and vanilla JavaScript frontend. Features natural language processing with spaCy and intelligent date parsing.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation & Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy English model
python -m spacy download en_core_web_sm

# 5. Run the application
python app.py
```

### Access the Application
Open your browser and navigate to: **http://127.0.0.1:5000**

## 📋 Features

### Backend Features
- ✅ **Flask REST API** with structured JSON responses
- ✅ **SQLite Database** for persistent booking storage
- ✅ **spaCy NLP** for name extraction and entity recognition
- ✅ **Natural Date Parsing** with dateparser library
- ✅ **Session Management** with UUID-based tracking
- ✅ **Input Validation** on both client and server side
- ✅ **Error Handling** with user-friendly messages

### Frontend Features
- ✅ **Responsive Design** - Mobile-friendly interface
- ✅ **Accessibility Support** - Screen reader compatible, keyboard navigation
- ✅ **Real-time Validation** - Input hints and error messages
- ✅ **Loading Indicators** - Visual feedback during API calls
- ✅ **Booking Confirmation Modal** - Complete reservation summary
- ✅ **Session Persistence** - Maintains conversation across page reloads

### NLP Capabilities
- ✅ **Name Recognition** - Extracts person names from natural text
- ✅ **Date Understanding** - Parses "tomorrow", "Jan 15th", "2024-01-15"
- ✅ **Guest Count Detection** - Understands "2 people", "just me", "three guests"
- ✅ **Yes/No Detection** - Fuzzy matching for confirmation responses
- ✅ **Date Validation** - Ensures checkout > checkin dates

## 🗂️ Project Structure

```
hotel-booking-chatbot/
├── app.py                 # Flask backend with SQLite integration
├── nlp_utils.py          # NLP helper functions using spaCy
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html       # Single-page chat interface
├── static/
│   ├── chat.css        # Responsive styles with CSS variables
│   └── chat.js         # Vanilla JavaScript chat functionality
├── bookings.db          # SQLite database (auto-created)
└── README.md           # This file
```

## 💬 Sample Conversation

Here's a typical booking conversation:

```
🤖 Bot: Hello! Welcome to our hotel booking service. Let's get started!
        What's your name?

👤 User: Hi, I'm John Smith

🤖 Bot: Nice to meet you, John Smith! When would you like to check in?
        (e.g., 'tomorrow', 'January 15th', '2024-01-15')

👤 User: tomorrow

🤖 Bot: Great! Check-in on 2024-01-16. When would you like to check out?

👤 User: January 20th

🤖 Bot: Perfect! Check-out on 2024-01-20. How many guests will be staying?

👤 User: 2 people

🤖 Bot: Noted: 2 guests. Would you like to include breakfast? (yes/no)

👤 User: yes please

🤖 Bot: Excellent, with breakfast! What's your preferred payment method?
        (credit card, debit card, cash, paypal, or 'skip')

👤 User: credit card

🤖 Bot: Please confirm your booking details:

        • Name: John Smith
        • Check-in: 2024-01-16
        • Check-out: 2024-01-20
        • Guests: 2
        • Breakfast: Yes
        • Payment: Credit Card

        Type 'confirm' to complete your booking or 'cancel' to start over.

👤 User: confirm

🤖 Bot: 🎉 Booking confirmed! Your reservation ID is #1. Thank you for choosing our hotel!

[Booking confirmation modal displays with complete details]
```

## 🛠️ API Endpoints

### GET /
Serves the main chat interface (`templates/index.html`)

### POST /api/chat
Handles chat messages and returns bot responses.

**Request:**
```json
{
    "message": "user input text",
    "session_id": "optional-uuid-string"
}
```

**Response:**
```json
{
    "reply": "bot response text",
    "complete": false,
    "booking": null,
    "session_id": "session-uuid"
}
```

**Booking Complete Response:**
```json
{
    "reply": "🎉 Booking confirmed! Your reservation ID is #1.",
    "complete": true,
    "booking": {
        "id": 1,
        "session_id": "uuid",
        "name": "John Smith",
        "checkin": "2024-01-16",
        "checkout": "2024-01-20",
        "guests": 2,
        "breakfast": true,
        "payment_method": "Credit Card",
        "created_at": "2024-01-15 14:30:00"
    },
    "session_id": "session-uuid"
}
```

## 🗃️ Database Schema

The SQLite database (`bookings.db`) contains a single table:

```sql
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    checkin TEXT NOT NULL,           -- ISO date format (YYYY-MM-DD)
    checkout TEXT NOT NULL,          -- ISO date format (YYYY-MM-DD)
    guests INTEGER NOT NULL,         -- Number of guests (1-10)
    breakfast BOOLEAN DEFAULT 0,     -- Breakfast included (0/1)
    payment_method TEXT,             -- Payment method or "Not specified"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Viewing Saved Bookings

Bookings are automatically saved to `bookings.db`. You can view them using:

```bash
# Install sqlite3 command line tool, then:
sqlite3 bookings.db "SELECT * FROM bookings;"

# Or use a GUI tool like DB Browser for SQLite
```

## 🔧 Configuration & Customization

### NLP Settings
Edit `nlp_utils.py` to customize:
- **Date formats**: Change `DATE_ORDER` in `parse_date()` function
- **Language support**: Replace spaCy model (`en_core_web_sm` → `de_core_news_sm` for German)
- **Fuzzy matching thresholds**: Adjust similarity scores in `is_yes()` and `parse_guests()`

### Frontend Customization
Edit `static/chat.css` CSS variables:
```css
:root {
    --primary-color: #4a90e2;      /* Change primary blue */
    --secondary-color: #28a745;    /* Change success green */
    --background-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Backend Configuration
Edit `app.py` constants:
```python
DATABASE_PATH = 'bookings.db'      # Database file location
SESSION_TIMEOUT = 3600             # Session timeout (seconds)
```

## 🔄 Adapting to Other Backends

### Integration with Rasa
To use with Rasa instead of the built-in NLP:

1. **Replace NLP functions** in `app.py`:
```python
# Replace this import:
from nlp_utils import extract_name, parse_date, is_yes, parse_guests

# With Rasa API calls:
import requests

def call_rasa_nlu(text, session_id):
    response = requests.post('http://localhost:5005/webhooks/rest/webhook',
                           json={'message': text, 'sender': session_id})
    return response.json()
```

2. **Update conversation flow** in `process_conversation_step()` to use Rasa intents and entities.

### PostgreSQL Migration
To switch from SQLite to PostgreSQL:

1. **Update requirements.txt**:
```txt
psycopg2-binary==2.9.7
```

2. **Replace database functions** in `app.py`:
```python
import psycopg2
from psycopg2.extras import RealDictCursor

def init_database():
    conn = psycopg2.connect(
        host="localhost",
        database="hotel_bookings",
        user="your_user",
        password="your_password"
    )
    # ... update schema creation
```

## 🧪 Testing the Application

### Manual Testing Checklist
- [ ] Name extraction with various formats
- [ ] Date parsing with natural language ("tomorrow", "next Friday")
- [ ] Date validation (checkout after checkin)
- [ ] Guest count detection (numbers and words)
- [ ] Yes/no recognition with fuzzy matching
- [ ] Session persistence across page refresh
- [ ] Mobile responsiveness
- [ ] Keyboard accessibility (Tab navigation)
- [ ] Screen reader compatibility

### Sample Test Cases

**Name extraction:**
- "Hi, I'm John Smith" → "John Smith"
- "My name is Alice" → "Alice"
- "Call me Bob" → "Bob"

**Date parsing:**
- "tomorrow" → Next day in YYYY-MM-DD format
- "January 15th" → "2024-01-15" (current year)
- "15/01/2024" → "2024-01-15"

**Guest count:**
- "2 people" → 2
- "just me" → 1
- "five guests" → 5

## 🔒 Security Considerations

- ✅ **XSS Prevention**: All user input is properly escaped
- ✅ **Input Validation**: Both client and server-side validation
- ✅ **SQL Injection Protection**: Uses parameterized queries
- ✅ **CSRF Protection**: Same-origin API requests
- ❌ **Authentication**: Not implemented (demo application)
- ❌ **Rate Limiting**: Not implemented (add for production)

## 📱 Browser Compatibility

**Supported Browsers:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Features Used:**
- ES6 Classes and Arrow Functions
- Fetch API
- CSS Grid and Flexbox
- CSS Custom Properties (Variables)

## 🐛 Troubleshooting

### Common Issues

**spaCy model not found:**
```bash
python -m spacy download en_core_web_sm
```

**Database locked error:**
```bash
# Check if another process is using the database
lsof bookings.db
```

**Port 5000 already in use:**
```python
# Edit app.py, change port:
app.run(debug=True, host='127.0.0.1', port=5001)
```

**JavaScript console errors:**
- Check browser developer tools (F12)
- Ensure all static files are loading correctly
- Verify API endpoint is responding

## 📝 License

This project is created for educational purposes. Feel free to use and modify for your own learning and development.

---

**Author**: AI Assistant
**Created**: 2024
**Technologies**: Flask, SQLite, spaCy, Vanilla JavaScript