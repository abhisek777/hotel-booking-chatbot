"""
Flask backend for hotel booking chatbot.
Handles conversation flow, SQLite database operations, and API endpoints.
"""

import os
import sqlite3
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from flask import Flask, render_template, request, jsonify

# Import NLP utilities - replace with your preferred NLP library if needed
try:
    from nlp_utils import extract_name, parse_date, is_yes, parse_guests, validate_date_order
except ImportError as e:
    print(f"Error importing NLP utilities: {e}")
    print("Please ensure nlp_utils.py is in the same directory and dependencies are installed.")
    exit(1)

app = Flask(__name__)

# Configuration
DATABASE_PATH = 'bookings.db'
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# In-memory session storage: {session_id: conversation_state}
# For production, consider using Redis or another persistent store
active_sessions: Dict[str, Dict[str, Any]] = {}


def init_database() -> None:
    """
    Initialize SQLite database and create bookings table if it doesn't exist.
    Call this on app startup to ensure database schema is ready.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create bookings table with all required fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            name TEXT NOT NULL,
            checkin TEXT NOT NULL,
            checkout TEXT NOT NULL,
            guests INTEGER NOT NULL,
            breakfast BOOLEAN DEFAULT 0,
            payment_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at: {os.path.abspath(DATABASE_PATH)}")


def save_booking_to_db(session_id: str, booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save completed booking to SQLite database.

    Args:
        session_id: Unique session identifier
        booking_data: Dictionary containing booking information

    Returns:
        Dictionary with booking record including database ID
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Insert booking record
    cursor.execute('''
        INSERT INTO bookings (session_id, name, checkin, checkout, guests, breakfast, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        booking_data['name'],
        booking_data['checkin_date'],
        booking_data['checkout_date'],
        booking_data['guests'],
        booking_data.get('breakfast', False),
        booking_data.get('payment_method', 'Not specified')
    ))

    booking_id = cursor.lastrowid
    conn.commit()

    # Retrieve the complete record with timestamp
    cursor.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    record = cursor.fetchone()
    conn.close()

    # Convert database row to dictionary
    if record:
        return {
            'id': record[0],
            'session_id': record[1],
            'name': record[2],
            'checkin': record[3],
            'checkout': record[4],
            'guests': record[5],
            'breakfast': bool(record[6]),
            'payment_method': record[7],
            'created_at': record[8]
        }
    return {}


def get_or_create_session(session_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Get existing session or create new one.

    Args:
        session_id: Optional existing session ID

    Returns:
        Tuple of (session_id, session_state)
    """
    if session_id and session_id in active_sessions:
        return session_id, active_sessions[session_id]

    # Create new session
    new_session_id = str(uuid.uuid4())
    session_state = {
        'step': 'name',  # Current conversation step
        'data': {},      # Collected booking data
        'created_at': datetime.now().isoformat()
    }

    active_sessions[new_session_id] = session_state
    return new_session_id, session_state


def process_conversation_step(session_state: Dict[str, Any], user_message: str) -> Dict[str, Any]:
    """
    Process user message based on current conversation step.

    Args:
        session_state: Current session state
        user_message: User's input message

    Returns:
        Dictionary with reply, completion status, and booking data if complete
    """
    step = session_state['step']
    data = session_state['data']

    # Step 1: Collect name
    if step == 'name':
        name = extract_name(user_message)
        if name:
            data['name'] = name
            session_state['step'] = 'checkin'
            return {
                'reply': f"Nice to meet you, {name}! When would you like to check in? (e.g., 'tomorrow', 'January 15th', '2024-01-15')",
                'complete': False,
                'booking': None
            }
        else:
            return {
                'reply': "I didn't catch your name. Could you please tell me your name?",
                'complete': False,
                'booking': None
            }

    # Step 2: Collect check-in date
    elif step == 'checkin':
        checkin_date = parse_date(user_message, prefer_future=True)
        if checkin_date:
            data['checkin_date'] = checkin_date
            session_state['step'] = 'checkout'
            return {
                'reply': f"Great! Check-in on {checkin_date}. When would you like to check out?",
                'complete': False,
                'booking': None
            }
        else:
            return {
                'reply': "I couldn't understand the date. Please provide your check-in date (e.g., 'tomorrow', 'January 15th', or '2024-01-15')",
                'complete': False,
                'booking': None
            }

    # Step 3: Collect check-out date
    elif step == 'checkout':
        checkout_date = parse_date(user_message, prefer_future=True)
        if checkout_date:
            # Validate that checkout is after checkin
            if validate_date_order(data['checkin_date'], checkout_date):
                data['checkout_date'] = checkout_date
                session_state['step'] = 'guests'
                return {
                    'reply': f"Perfect! Check-out on {checkout_date}. How many guests will be staying?",
                    'complete': False,
                    'booking': None
                }
            else:
                return {
                    'reply': f"Check-out date must be after check-in date ({data['checkin_date']}). Please provide a later check-out date.",
                    'complete': False,
                    'booking': None
                }
        else:
            return {
                'reply': "I couldn't understand the check-out date. Please provide a valid date.",
                'complete': False,
                'booking': None
            }

    # Step 4: Collect number of guests
    elif step == 'guests':
        guests = parse_guests(user_message)
        if guests:
            data['guests'] = guests
            session_state['step'] = 'breakfast'
            guest_text = "guest" if guests == 1 else "guests"
            return {
                'reply': f"Noted: {guests} {guest_text}. Would you like to include breakfast? (yes/no)",
                'complete': False,
                'booking': None
            }
        else:
            return {
                'reply': "Please tell me the number of guests (1-10 people).",
                'complete': False,
                'booking': None
            }

    # Step 5: Optional breakfast preference
    elif step == 'breakfast':
        breakfast_response = is_yes(user_message)
        if breakfast_response is not None:
            data['breakfast'] = breakfast_response
            session_state['step'] = 'payment'
            breakfast_text = "with breakfast" if breakfast_response else "without breakfast"
            return {
                'reply': f"Excellent, {breakfast_text}! What's your preferred payment method? (credit card, debit card, cash, paypal, or 'skip')",
                'complete': False,
                'booking': None
            }
        else:
            return {
                'reply': "Please answer yes or no for breakfast preference.",
                'complete': False,
                'booking': None
            }

    # Step 6: Optional payment method
    elif step == 'payment':
        payment_method = user_message.strip().lower()

        # Allow skipping payment method
        if payment_method in ['skip', 'later', 'none']:
            data['payment_method'] = 'Not specified'
        else:
            # Validate payment method (basic fuzzy matching)
            valid_methods = ['credit card', 'debit card', 'cash', 'paypal']
            best_match = None
            best_score = 0

            for method in valid_methods:
                from rapidfuzz import fuzz
                score = fuzz.ratio(payment_method, method)
                if score > best_score and score > 60:  # Lower threshold for flexibility
                    best_score = score
                    best_match = method

            if best_match:
                data['payment_method'] = best_match.title()
            else:
                data['payment_method'] = payment_method.title()

        session_state['step'] = 'confirm'

        # Generate booking summary
        summary = f"""
Please confirm your booking details:

• Name: {data['name']}
• Check-in: {data['checkin_date']}
• Check-out: {data['checkout_date']}
• Guests: {data['guests']}
• Breakfast: {'Yes' if data.get('breakfast', False) else 'No'}
• Payment: {data.get('payment_method', 'Not specified')}

Type 'confirm' to complete your booking or 'cancel' to start over.
"""
        return {
            'reply': summary.strip(),
            'complete': False,
            'booking': None
        }

    # Step 7: Final confirmation
    elif step == 'confirm':
        response = user_message.lower().strip()

        if response in ['confirm', 'yes', 'book', 'book it', 'proceed']:
            # Save to database and complete booking
            booking_record = save_booking_to_db(session_state.get('session_id', ''), data)

            # Mark session as complete
            session_state['step'] = 'complete'

            return {
                'reply': f"🎉 Booking confirmed! Your reservation ID is #{booking_record['id']}. Thank you for choosing our hotel!",
                'complete': True,
                'booking': booking_record
            }

        elif response in ['cancel', 'no', 'restart', 'start over']:
            # Reset session
            session_state['step'] = 'name'
            session_state['data'] = {}
            return {
                'reply': "Booking cancelled. Let's start over! What's your name?",
                'complete': False,
                'booking': None
            }

        else:
            return {
                'reply': "Please type 'confirm' to complete your booking or 'cancel' to start over.",
                'complete': False,
                'booking': None
            }

    # Default case - should not reach here in normal flow
    else:
        session_state['step'] = 'name'
        session_state['data'] = {}
        return {
            'reply': "Let's start over! What's your name?",
            'complete': False,
            'booking': None
        }


@app.route('/')
def index():
    """Serve the main chat page."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    Handle chat messages via REST API.

    Expected JSON payload:
    {
        "message": "user input text",
        "session_id": "optional session identifier"
    }

    Returns JSON response:
    {
        "reply": "bot response text",
        "complete": false,
        "booking": null,
        "session_id": "session identifier"
    }
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()

        # Validate required fields
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing required field: message'
            }), 400

        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'error': 'Message cannot be empty'
            }), 400

        # Get or create session
        session_id, session_state = get_or_create_session(data.get('session_id'))
        session_state['session_id'] = session_id  # Store session_id in state for database operations

        # Process the conversation step
        response = process_conversation_step(session_state, user_message)
        response['session_id'] = session_id

        return jsonify(response)

    except Exception as e:
        # Log error in production, return generic error to client
        print(f"Chat endpoint error: {e}")
        return jsonify({
            'error': 'Internal server error. Please try again.',
            'session_id': session_id if 'session_id' in locals() else None
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("Initializing Hotel Booking Chatbot...")

    # Initialize database on startup
    try:
        init_database()
    except Exception as e:
        print(f"Database initialization failed: {e}")
        exit(1)

    print("Starting Flask server...")
    print("Visit: http://127.0.0.1:5000")
    print(f"Bookings will be saved to: {os.path.abspath(DATABASE_PATH)}")

    # Run Flask app (change host/port as needed)
    app.run(
        debug=True,      # Set to False for production
        host='127.0.0.1',
        port=5000
    )