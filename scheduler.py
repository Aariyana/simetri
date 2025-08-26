"""
Job scheduler for automating scraping and posting tasks
"""

import schedule
import threading
import time
import logging
from datetime import datetime
from typing import List, Dict
from config import Config
from scrapers.sarkari_result import SarkariResultScraper
from scrapers.freshers_world import FreshersWorldScraper
from scrapers.naukri import NaukriScraper
from job_processor import JobProcessor
from telegram_bot import run_telegram_posting
from blogger_client import BloggerJobPoster

logger = logging.getLogger(__name__)

class JobScheduler:
    """Schedule and manage automated job scraping and posting"""
    
    def __init__(self):
        self.config = Config()
        self.job_processor = JobProcessor(self.config)
        self.blogger_poster = BloggerJobPoster(self.config)
        self.running = False
        
        # Initialize scrapers
        self.scrapers = []
        if self.config.SCRAPING_SOURCES['sarkari_result']['enabled']:
            self.scrapers.append(SarkariResultScraper(self.config))
        if self.config.SCRAPING_SOURCES['freshers_world']['enabled']:
            self.scrapers.append(FreshersWorldScraper(self.config))
        if self.config.SCRAPING_SOURCES['naukri']['enabled']:
            self.scrapers.append(NaukriScraper(self.config))
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting job scheduler")
        
        # Schedule scraping tasks
        interval_hours = self.config.SCRAPING_INTERVAL // 3600  # Convert seconds to hours
        schedule.every(interval_hours).hours.do(self.run_scraping_job)
        
        # Schedule posting tasks (30 minutes after scraping)
        schedule.every(interval_hours).hours.do(self.run_posting_job).tag('posting')
        
        # Schedule daily cleanup
        schedule.every().day.at("02:00").do(self.run_cleanup_job)
        
        # Schedule status updates
        schedule.every(6).hours.do(self.send_status_update)
        
        # Run initial scraping job
        logger.info("Running initial scraping job")
        threading.Thread(target=self.run_scraping_job, daemon=True).start()
        
        # Start the schedule runner
        self.run_scheduler()
    
    def run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")
    
    def run_scraping_job(self):
        """Run the scraping job"""
        logger.info("Starting scheduled scraping job")
        start_time = datetime.now()
        
        try:
            all_scraped_jobs = []
            
            # Run each scraper
            for scraper in self.scrapers:
                try:
                    logger.info(f"Running scraper: {scraper.get_source_name()}")
                    jobs = scraper.scrape_jobs()
                    all_scraped_jobs.extend(jobs)
                    logger.info(f"Scraped {len(jobs)} jobs from {scraper.get_source_name()}")
                    
                    # Add delay between scrapers
                    time.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in scraper {scraper.get_source_name()}: {e}")
                    continue
            
            # Process scraped jobs
            new_jobs = self.job_processor.process_jobs(all_scraped_jobs)
            
            # Schedule posting job for 30 minutes later
            if new_jobs:
                schedule.every(30).minutes.do(self.run_posting_job_for_jobs, new_jobs).tag('delayed_posting')
            
            duration = datetime.now() - start_time
            logger.info(f"Scraping job completed in {duration.total_seconds():.1f} seconds. Found {len(new_jobs)} new jobs.")
            
        except Exception as e:
            logger.error(f"Error in scraping job: {e}")
    
    def run_posting_job(self):
        """Run the posting job for all unposted jobs"""
        logger.info("Starting scheduled posting job")
        
        try:
            # Get jobs ready for posting
            jobs_to_post = self.job_processor.get_jobs_for_posting(limit=self.config.MAX_JOBS_PER_POST * 3)
            
            if not jobs_to_post:
                logger.info("No jobs to post")
                return
            
            self.post_jobs(jobs_to_post)
            
        except Exception as e:
            logger.error(f"Error in posting job: {e}")
    
    def run_posting_job_for_jobs(self, jobs: List[Dict]):
        """Run posting job for specific jobs"""
        if not jobs:
            return
        
        logger.info(f"Running delayed posting job for {len(jobs)} jobs")
        
        try:
            self.post_jobs(jobs)
            
            # Remove the delayed posting task
            schedule.clear('delayed_posting')
            
        except Exception as e:
            logger.error(f"Error in delayed posting job: {e}")
    
    def post_jobs(self, jobs: List[Dict]):
        """Post jobs to Telegram and Blogger"""
        if not jobs:
            return
        
        start_time = datetime.now()
        success_telegram = False
        success_blogger = False
        
        try:
            # Post to Telegram
            logger.info("Posting jobs to Telegram")
            success_telegram = run_telegram_posting(self.config, jobs)
            
            # Small delay between services
            time.sleep(5)
            
            # Post to Blogger
            logger.info("Posting jobs to Blogger")
            success_blogger = self.blogger_poster.post_jobs_to_blogger(jobs)
            
            # Mark jobs as posted if at least one service succeeded
            if success_telegram or success_blogger:
                self.job_processor.mark_jobs_as_posted(jobs)
                
                services = []
                if success_telegram:
                    services.append("Telegram")
                if success_blogger:
                    services.append("Blogger")
                
                duration = datetime.now() - start_time
                logger.info(f"Successfully posted {len(jobs)} jobs to {', '.join(services)} in {duration.total_seconds():.1f} seconds")
            else:
                logger.error("Failed to post jobs to any service")
                
        except Exception as e:
            logger.error(f"Error posting jobs: {e}")
    
    def run_cleanup_job(self):
        """Run daily cleanup job"""
        logger.info("Running daily cleanup job")
        
        try:
            # Cleanup old job data (keep last 7 days)
            self.job_processor.cleanup_old_data(days=7)
            
            logger.info("Daily cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
    
    def send_status_update(self):
        """Send status update"""
        try:
            from telegram_bot import TelegramJobPoster
            import asyncio
            
            poster = TelegramJobPoster(self.config)
            
            # Get job statistics
            all_jobs = self.job_processor.storage.load_existing_jobs()
            posted_jobs = self.job_processor.storage.load_posted_jobs()
            
            total_jobs = len(all_jobs)
            total_posted = len(posted_jobs)
            unposted_jobs = len(self.job_processor.get_jobs_for_posting())
            
            # Calculate jobs by category
            gov_jobs = len([job for job in all_jobs if job.get('category') == 'government'])
            private_jobs = len([job for job in all_jobs if job.get('category') == 'private'])
            
            status_message = f"""
📊 <b>Bot Statistics</b>
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📈 <b>Job Counts:</b>
• Total Jobs Scraped: {total_jobs}
• Government Jobs: {gov_jobs}
• Private Jobs: {private_jobs}
• Jobs Posted: {total_posted}
• Jobs Pending: {unposted_jobs}

🔧 <b>Status:</b> ✅ Active
⏰ <b>Next Scraping:</b> As scheduled

🤖 Bot is working normally!
            """
            
            # Send status update asynchronously
            async def send_update():
                await poster.send_status_update(status_message)
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(send_update())
            
            logger.info("Status update sent")
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        next_jobs = schedule.jobs
        
        status = {
            'running': self.running,
            'scrapers_count': len(self.scrapers),
            'scheduled_jobs': len(next_jobs),
            'next_run': str(next_jobs[0].next_run) if next_jobs else None
        }
        
        return status
