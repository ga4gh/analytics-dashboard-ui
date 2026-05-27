from app.app import app
from app.config import config

server = app.server

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=config.ui_port)
