"""
Configuration file for Instagram Analytics Dashboard
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API Key (optional - for category/location inference)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)

# App Configuration
APP_TITLE = "Instagram Analytics Dashboard"
APP_ICON = "📊"

# Scraping Defaults
DEFAULT_MAX_POSTS = 50
DEFAULT_DELAY = 2
MIN_POSTS = 10
MAX_POSTS = 100
MIN_DELAY = 1
MAX_DELAY = 5
