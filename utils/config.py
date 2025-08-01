import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")
    
    @staticmethod
    def verify_config():
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Google API key is required. Please set GOOGLE_API_KEY in .env file.")
        if not Config.GOOGLE_CSE_ID:
            print("Warning: Google CSE ID not set. Some SEO features will be limited.")