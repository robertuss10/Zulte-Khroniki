"""
Zulte Kroniki Combined Application Runner
This script runs both the Discord bot and web dashboard together.
"""

import subprocess
import sys
import threading
import time
import logging
import os
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("combined_app.log"),
        logging.StreamHandler()
    ]
)

# Global variables to track subprocesses
bot_process = None
web_process = None

def start_bot():
    """Start the Discord bot in a background process"""
    global bot_process
    
    try:
        logging.info("Starting Discord bot process...")
        # Use the bot daemon for better process management
        bot_process = subprocess.Popen(
            [sys.executable, 'bot_daemon.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        # Log the process ID
        logging.info(f"Bot process started with PID {bot_process.pid}")
        
        # Monitor the process output
        for line in bot_process.stdout:
            line = line.strip()
            if line:
                logging.info(f"Bot: {line}")
    
    except Exception as e:
        logging.error(f"Error starting bot: {e}")

def start_web():
    """Start the web dashboard using Gunicorn"""
    global web_process
    
    try:
        logging.info("Starting web dashboard process...")
        # Use Gunicorn for production-ready web server
        web_process = subprocess.Popen(
            ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "main:app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        # Log the process ID
        logging.info(f"Web dashboard started with PID {web_process.pid}")
        
        # Monitor the process output
        for line in web_process.stdout:
            line = line.strip()
            if line:
                logging.info(f"Web: {line}")
    
    except Exception as e:
        logging.error(f"Error starting web: {e}")

def signal_handler(sig, frame):
    """Handle process termination"""
    logging.info("Shutting down Zulte Kroniki application...")
    
    if bot_process:
        logging.info(f"Terminating bot process (PID: {bot_process.pid})...")
        bot_process.terminate()
    
    if web_process:
        logging.info(f"Terminating web process (PID: {web_process.pid})...")
        web_process.terminate()
    
    logging.info("Shutdown complete.")
    sys.exit(0)

if __name__ == "__main__":
    logging.info("Starting Zulte Kroniki combined application...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start web dashboard in a separate thread
    web_thread = threading.Thread(target=start_web)
    web_thread.daemon = True
    web_thread.start()
    
    # Give the web dashboard a moment to start
    time.sleep(2)
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
            
            # Check if any process died and restart it
            if web_process and web_process.poll() is not None:
                logging.warning("Web dashboard process died, restarting...")
                web_thread = threading.Thread(target=start_web)
                web_thread.daemon = True
                web_thread.start()
            
            if bot_process and bot_process.poll() is not None:
                logging.warning("Bot process died, restarting...")
                bot_thread = threading.Thread(target=start_bot)
                bot_thread.daemon = True
                bot_thread.start()
    
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
