from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import requests
import json
import re
from typing import List, Dict, Any, Optional
from config import OPENROUTER_API_KEY, OPENROUTER_API_ENDPOINT, DATABASE_PATH, HOTEL_NAME

app = FastAPI(title="Hotel Booking Chatbot API")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Database Setup
# ---------------------------
def init_db():
    """Initialize the SQLite database with bookings table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            checkin_date TEXT,
            checkout_date TEXT,
            num_guests INTEGER,
            payment_method TEXT,
            breakfast_included BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ---------------------------
# Request / Response Models
# ---------------------------
class Message(BaseModel):
    id: int
    role: str
    text: str

class ChatRequest(BaseModel):
    system_prompt: str
    conversation: List[Message]
    user_message: str

class ChatResponse(BaseModel):
    reply: str
    booking_complete: bool = False
    booking_details: Optional[Dict[str, Any]] = None

class BookingDetails(BaseModel):
    name: Optional[str] = None
    checkin_date: Optional[str] = None
    checkout_date: Optional[str] = None
    num_guests: Optional[int] = None
    payment_method: Optional[str] = None
    breakfast_included: Optional[bool] = None

# ---------------------------
# Helper Functions
# ---------------------------
def extract_booking_details(conversation_text: str) -> BookingDetails:
    """Extract booking details from conversation text using regex patterns"""
    details = BookingDetails()
    
    # Extract name (look for patterns like "My name is..." or "I'm...")
    name_patterns = [
        r"(?:my name is|i'm|i am|call me)\s+([a-zA-Z\s]+)",
        r"name:\s*([a-zA-Z\s]+)"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match:
            details.name = match.group(1).strip().title()
            break
    
    # Extract dates (look for date patterns)
    date_patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{4}-\d{1,2}-\d{1,2})",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",
    ]
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, conversation_text, re.IGNORECASE)
        dates_found.extend(matches)
    
    if len(dates_found) >= 2:
        details.checkin_date = dates_found[0]
        details.checkout_date = dates_found[1]
    elif len(dates_found) == 1:
        details.checkin_date = dates_found[0]
    
    # Extract number of guests
    guest_patterns = [
        r"(\d+)\s+(?:guests?|people|persons?)",
        r"(?:guests?|people|persons?):\s*(\d+)",
        r"for\s+(\d+)\s+(?:guests?|people|persons?)"
    ]
    for pattern in guest_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match:
            details.num_guests = int(match.group(1))
            break
    
    # Extract payment method
    payment_patterns = [
        r"(?:credit card|visa|mastercard|amex|american express)",
        r"(?:cash|debit|paypal)",
        r"payment.*(?:credit|cash|debit|card)"
    ]
    for pattern in payment_patterns:
        match = re.search(pattern, conversation_text, re.IGNORECASE)
        if match:
            details.payment_method = match.group(0).title()
            break
    
    # Extract breakfast preference
    if re.search(r"(?:with|include|want|yes).*breakfast", conversation_text, re.IGNORECASE):
        details.breakfast_included = True
    elif re.search(r"(?:without|no|skip).*breakfast", conversation_text, re.IGNORECASE):
        details.breakfast_included = False
    
    return details

def save_booking(details: BookingDetails) -> int:
    """Save booking details to database and return booking ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO bookings (name, checkin_date, checkout_date, num_guests, payment_method, breakfast_included)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        details.name,
        details.checkin_date,
        details.checkout_date,
        details.num_guests,
        details.payment_method,
        details.breakfast_included or False
    ))
    
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return booking_id

def is_booking_complete(details: BookingDetails) -> bool:
    """Check if all mandatory booking details are present"""
    return all([
        details.name,
        details.checkin_date,
        details.checkout_date,
        details.num_guests
    ])

def generate_mock_response(user_message: str, conversation: List[Message]) -> str:
    """Generate mock chatbot responses for development/testing"""
    user_msg_lower = user_message.lower()
    conversation_count = len([msg for msg in conversation if msg.role == "user"])
    
    # Welcome message
    if conversation_count == 0 or "hello" in user_msg_lower or "hi" in user_msg_lower:
        return f"Welcome to {HOTEL_NAME}! I'm here to help you book a room. May I start by getting your name?"
    
    # Name collection
    if any(word in user_msg_lower for word in ["name", "i'm", "i am", "call me"]) and conversation_count <= 2:
        return "Thank you! Now, could you please tell me your preferred check-in and check-out dates?"
    
    # Date collection
    if any(word in user_msg_lower for word in ["date", "january", "february", "march", "april", "may", "june", 
                                               "july", "august", "september", "october", "november", "december",
                                               "/", "-"]) and conversation_count <= 4:
        return "Great! How many guests will be staying with us?"
    
    # Guest count
    if any(char.isdigit() for char in user_message) and "guest" not in user_msg_lower and conversation_count <= 6:
        return "Perfect! Would you prefer to pay by credit card or cash? Also, would you like to include breakfast with your stay?"
    
    # Payment and breakfast
    if any(word in user_msg_lower for word in ["credit", "cash", "card", "breakfast", "yes", "no"]) and conversation_count <= 8:
        return "Excellent! Let me confirm your booking details. I have all the information needed to process your reservation."
    
    # Default responses
    responses = [
        "Could you please provide more details about that?",
        "I understand. Is there anything else you'd like to add to your booking?",
        "Thank you for that information. What else can I help you with?",
        "I see. Let me know if you have any other preferences for your stay.",
        "That's noted. Is there anything specific you'd like to know about our hotel?"
    ]
    
    return responses[conversation_count % len(responses)]

# ---------------------------
# API Endpoints
# ---------------------------
@app.get("/")
def read_root():
    return {"message": f"Welcome to {HOTEL_NAME} Booking Chatbot API"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for processing user messages"""
    
    # Check if we're in mock mode (no API key provided)
    use_mock_mode = OPENROUTER_API_KEY == 'your_api_key_here'
    
    if use_mock_mode:
        # Mock chatbot responses for development/testing
        bot_reply = generate_mock_response(request.user_message, request.conversation)
    else:
        # Assemble the conversation messages for the LLM API
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": request.system_prompt}]
            }
        ]
        
        # Add all the conversation messages
        for msg in request.conversation:
            role = "user" if msg.role == "user" else "assistant"
            messages.append({
                "role": role,
                "content": [{"type": "text", "text": msg.text}]
            })
        
        # Add the latest user message
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": request.user_message}]
        })

        # Prepare payload for OpenRouter API
        payload = {
            "model": "openai/gpt-4o",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        }

        # Real API mode
        try:
            response = requests.post(OPENROUTER_API_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract the bot reply
            bot_reply = data.get('choices', [{}])[0].get('message', {}).get('content', 'Sorry, I could not process your request.')
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    # Extract booking details from the entire conversation
    full_conversation = " ".join([msg.text for msg in request.conversation] + [request.user_message])
    booking_details = extract_booking_details(full_conversation)
    
    # Check if booking is complete
    booking_complete = is_booking_complete(booking_details)
    booking_id = None
    
    if booking_complete:
        try:
            booking_id = save_booking(booking_details)
            bot_reply += f"\n\nGreat! Your booking has been confirmed with ID #{booking_id}. Thank you for choosing {HOTEL_NAME}!"
        except Exception as db_err:
            print(f"Database insertion failed: {db_err}")
            bot_reply += "\n\nYour booking details have been recorded, but there was an issue saving to our system. Please contact our support team."
    
    return ChatResponse(
        reply=bot_reply,
        booking_complete=booking_complete,
        booking_details=booking_details.dict() if booking_complete else None
    )

@app.get("/bookings")
def get_bookings():
    """Get all bookings from the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC")
        bookings = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        booking_list = []
        for booking in bookings:
            booking_list.append({
                "id": booking[0],
                "name": booking[1],
                "checkin_date": booking[2],
                "checkout_date": booking[3],
                "num_guests": booking[4],
                "payment_method": booking[5],
                "breakfast_included": booking[6],
                "created_at": booking[7]
            })
        
        return {"bookings": booking_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
