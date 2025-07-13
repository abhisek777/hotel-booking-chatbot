#!/usr/bin/env python3
"""
Startup script for the Hotel Booking Chatbot Backend
"""

import os
import sys
import subprocess
import sqlite3
from config import DATABASE_PATH, HOTEL_NAME

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ['fastapi', 'uvicorn', 'requests', 'pydantic']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    return True

def setup_database():
    """Initialize the database"""
    try:
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
        print(f"✓ Database initialized: {DATABASE_PATH}")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print(f"\n🏨 Starting {HOTEL_NAME} Booking Chatbot API...")
    print("📡 Server will be available at: http://localhost:8001")
    print("📚 API documentation: http://localhost:8001/docs")
    print("🔄 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "server:app", 
            "--host", "0.0.0.0", 
            "--port", "8001", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"✗ Failed to start server: {e}")

def main():
    """Main startup function"""
    print(f"🚀 {HOTEL_NAME} Booking Chatbot Backend")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
