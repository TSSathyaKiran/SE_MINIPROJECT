"""Start the app:  python src/run.py   ->  http://localhost:8000
(Not 5000: macOS uses that port for AirPlay.)"""
import os

from app import create_app

app = create_app("dev")

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", "8000")))
