"""
Database initialization script for hotel booking chatbot.

This script creates the SQLite database and bookings table.
It's optional since app.py automatically initializes the database on startup,
but useful for manual setup or testing.

Usage:
    python init_db.py
"""

import os
import sqlite3
from datetime import datetime

DATABASE_PATH = 'bookings.db'


def create_database():
    """
    Create SQLite database and bookings table.

    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        # Connect to SQLite database (creates file if doesn't exist)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Create bookings table with all required columns
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

        # Create index on session_id for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_id ON bookings(session_id)
        ''')

        # Create index on created_at for chronological queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON bookings(created_at)
        ''')

        # Commit changes
        conn.commit()
        conn.close()

        print(f"✅ Database created successfully at: {os.path.abspath(DATABASE_PATH)}")
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def add_sample_data():
    """
    Add sample booking data for testing purposes.

    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Sample booking data
        sample_bookings = [
            {
                'session_id': 'sample-session-1',
                'name': 'John Smith',
                'checkin': '2024-01-15',
                'checkout': '2024-01-18',
                'guests': 2,
                'breakfast': True,
                'payment_method': 'Credit Card'
            },
            {
                'session_id': 'sample-session-2',
                'name': 'Alice Johnson',
                'checkin': '2024-01-20',
                'checkout': '2024-01-22',
                'guests': 1,
                'breakfast': False,
                'payment_method': 'PayPal'
            },
            {
                'session_id': 'sample-session-3',
                'name': 'Bob Wilson',
                'checkin': '2024-01-25',
                'checkout': '2024-01-28',
                'guests': 4,
                'breakfast': True,
                'payment_method': 'Debit Card'
            }
        ]

        # Insert sample data
        for booking in sample_bookings:
            cursor.execute('''
                INSERT INTO bookings (session_id, name, checkin, checkout, guests, breakfast, payment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                booking['session_id'],
                booking['name'],
                booking['checkin'],
                booking['checkout'],
                booking['guests'],
                booking['breakfast'],
                booking['payment_method']
            ))

        conn.commit()
        conn.close()

        print(f"✅ Added {len(sample_bookings)} sample bookings to database")
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error while adding sample data: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error while adding sample data: {e}")
        return False


def view_bookings():
    """
    Display all bookings in the database.
    """
    try:
        if not os.path.exists(DATABASE_PATH):
            print(f"❌ Database file not found: {DATABASE_PATH}")
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get all bookings ordered by creation date
        cursor.execute('''
            SELECT id, session_id, name, checkin, checkout, guests, breakfast, payment_method, created_at
            FROM bookings
            ORDER BY created_at DESC
        ''')

        bookings = cursor.fetchall()
        conn.close()

        if not bookings:
            print("📭 No bookings found in database")
            return

        print(f"\n📋 Found {len(bookings)} booking(s):")
        print("-" * 100)
        print(f"{'ID':<3} {'Name':<15} {'Check-in':<12} {'Check-out':<12} {'Guests':<7} {'Breakfast':<10} {'Payment':<15} {'Created':<20}")
        print("-" * 100)

        for booking in bookings:
            id_, session_id, name, checkin, checkout, guests, breakfast, payment_method, created_at = booking
            breakfast_str = 'Yes' if breakfast else 'No'

            print(f"{id_:<3} {name:<15} {checkin:<12} {checkout:<12} {guests:<7} {breakfast_str:<10} {payment_method:<15} {created_at:<20}")

        print("-" * 100)

    except sqlite3.Error as e:
        print(f"❌ Database error while viewing bookings: {e}")
    except Exception as e:
        print(f"❌ Unexpected error while viewing bookings: {e}")


def clear_database():
    """
    Clear all bookings from the database (keeps table structure).

    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        if not os.path.exists(DATABASE_PATH):
            print(f"❌ Database file not found: {DATABASE_PATH}")
            return False

        response = input("⚠️  Are you sure you want to delete ALL bookings? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return False

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Delete all bookings
        cursor.execute('DELETE FROM bookings')

        # Reset auto-increment counter
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="bookings"')

        conn.commit()
        conn.close()

        print("✅ All bookings cleared from database")
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error while clearing bookings: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error while clearing bookings: {e}")
        return False


def main():
    """
    Main function with interactive menu.
    """
    print("🏨 Hotel Booking Database Setup")
    print("================================")

    while True:
        print("\nChoose an option:")
        print("1. Create/Initialize database")
        print("2. Add sample booking data")
        print("3. View all bookings")
        print("4. Clear all bookings")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '1':
            create_database()
        elif choice == '2':
            if os.path.exists(DATABASE_PATH):
                add_sample_data()
            else:
                print("❌ Database not found. Please create it first (option 1)")
        elif choice == '3':
            view_bookings()
        elif choice == '4':
            clear_database()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == '__main__':
    main()