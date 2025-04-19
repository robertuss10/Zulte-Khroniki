#!/usr/bin/env python3
"""
Restart script for Zulte Kroniki application.
This script stops all running processes and then starts everything cleanly.
"""
import os
import sys
import subprocess
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def kill_processes(process_names):
    """Kill processes by name"""
    for name in process_names:
        logging.info(f"Stopping {name} processes...")
        try:
            # Find PIDs for the process
            result = subprocess.run(
                ["pgrep", "-f", name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    try:
                        pid = int(pid.strip())
                        logging.info(f"Killing process with PID {pid}")
                        os.kill(pid, signal.SIGTERM)
                    except (ValueError, ProcessLookupError) as e:
                        logging.warning(f"Error killing process {pid}: {e}")
        except Exception as e:
            logging.error(f"Error finding {name} processes: {e}")

def start_web_dashboard():
    """Start the web dashboard"""
    logging.info("Starting web dashboard...")
    subprocess.Popen(
        ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "main:app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def start_discord_bot():
    """Start the Discord bot"""
    logging.info("Starting Discord bot...")
    subprocess.Popen(
        [sys.executable, "bot_daemon.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

if __name__ == "__main__":
    # Process names to kill
    processes_to_kill = [
        "gunicorn",
        "start_bot.py",
        "bot_daemon.py",
        "run.py"
    ]
    
    # Kill all running processes
    kill_processes(processes_to_kill)
    
    # Wait a moment to ensure all processes are terminated
    logging.info("Waiting for processes to terminate...")
    time.sleep(2)
    
    # Start the web dashboard
    start_web_dashboard()
    
    # Wait for web dashboard to initialize
    logging.info("Waiting for web dashboard to initialize...")
    time.sleep(2)
    
    # Start the Discord bot
    start_discord_bot()
    
    logging.info("All services restarted successfully!")