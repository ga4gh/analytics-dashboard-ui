import os

class Config:

    def __init__(self):
        self.api_base_url = os.getenv("GA4GH_ANALYTICS_DASHBOARD_API_BASE_URL", "http://localhost:8000")
        self.ui_port = int(os.getenv("GA4GH_ANALYTICS_DASHBOARD_UI_PORT", 8050))

config = Config()
