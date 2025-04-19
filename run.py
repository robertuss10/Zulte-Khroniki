import threading
import logging
from bot import run_bot
from app import run_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Zulte Kroniki Bot and Web Dashboard")
    
    # Start bot and web app in separate threads
    bot_thread = threading.Thread(target=run_bot)
    app_thread = threading.Thread(target=run_app)
    
    bot_thread.start()
    app_thread.start()
    
    logger.info("Bot and Web Dashboard started successfully")
    
    # Wait for threads to complete
    try:
        bot_thread.join()
        app_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")