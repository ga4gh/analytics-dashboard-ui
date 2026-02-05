import os

class Settings:
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

settings = Settings()
