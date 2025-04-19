"""
Zulte Kroniki Discord Bot Daemon
This script runs the Discord bot in a manner that ensures it stays connected.
"""
import os
import sys
import time
import subprocess
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot_daemon.log"),
        logging.StreamHandler()
    ]
)

def run_bot():
    """Run the bot as a subprocess and handle restarts"""
    bot_process = None
    
    def signal_handler(sig, frame):
        """Handle shutdown signals"""
        if bot_process:
            logging.info("Stopping bot process...")
            bot_process.terminate()
        logging.info("Bot daemon shutting down.")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while True:
        try:
            logging.info("Starting Discord bot process...")
            # Use subprocess to run the bot
            bot_process = subprocess.Popen(
                [sys.executable, 'start_bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            # Monitor the bot process
            while bot_process.poll() is None:
                # Read and forward output
                if bot_process.stdout:
                    line = bot_process.stdout.readline().strip()
                    if line:
                        logging.info(f"Bot: {line}")
                time.sleep(0.1)
            
            exit_code = bot_process.returncode
            logging.warning(f"Bot process exited with code {exit_code}")
            
            # If the bot exited normally, don't restart immediately
            if exit_code == 0:
                logging.info("Bot shut down normally. Exiting daemon.")
                break
            
            # Wait before restarting to avoid rapid restart loops
            logging.info("Waiting 10 seconds before restarting...")
            time.sleep(10)
            
        except Exception as e:
            logging.error(f"Error in bot daemon: {e}")
            if bot_process and bot_process.poll() is None:
                bot_process.terminate()
            time.sleep(10)  # Wait before retry

if __name__ == "__main__":
    logging.info("Starting Zulte Kroniki Bot Daemon...")
    run_bot()