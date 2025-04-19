"""
Zulte Kroniki Combined Application Runner
This script runs both the Discord bot and web dashboard together.
"""

import threading
import time
from app import run_app
from bot import run_bot

if __name__ == "__main__":
    print("Starting Zulte Kroniki combined application...")
    print("* Starting web dashboard...")

    # Start web dashboard in a separate thread
    web_thread = threading.Thread(target=run_app)
    web_thread.daemon = True
    web_thread.start()

    # Give the web dashboard a moment to start
    time.sleep(2)

    print("* Starting Discord bot...")
    # Run the Discord bot in the main thread
    run_bot()
