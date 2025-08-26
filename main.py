#!/usr/bin/env python3
"""
Indian Government Job Posting Telegram Bot
Main entry point for the application
"""

import logging
import threading
import time
import os
from web_app import app
from scheduler import JobScheduler
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_web_app():
    """Run the Flask web application"""
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start web application: {e}")

def run_scheduler():
    """Run the job scheduler"""
    try:
        scheduler = JobScheduler()
        scheduler.start()
        
        # Keep the scheduler running
        while True:
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")

def main():
    """Main application entry point"""
    logger.info("Starting Indian Job Bot Application")
    
    # Verify configuration
    config = Config()
    if not config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        return
    
    # Create threads for web app and scheduler
    web_thread = threading.Thread(target=run_web_app, daemon=True)
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    
    try:
        # Start both threads
        web_thread.start()
        logger.info("Web application started on http://0.0.0.0:5000")
        
        scheduler_thread.start()
        logger.info("Job scheduler started")
        
        # Wait for threads to complete (or run indefinitely)
        web_thread.join()
        scheduler_thread.join()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
