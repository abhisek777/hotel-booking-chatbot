import os

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', 'your_api_key_here')
OPENROUTER_API_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# Database configuration
DATABASE_PATH = "hotel_booking.db"

# Hotel configuration
HOTEL_NAME = "Grand Riviera Hotel"
