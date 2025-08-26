"""
Telegram bot integration for posting jobs
"""

import asyncio
import logging
from typing import List, Dict
from telegram import Bot
from telegram.error import TelegramError
from config import Config

logger = logging.getLogger(__name__)

class TelegramJobPoster:
    """Handle Telegram bot operations for job posting"""
    
    def __init__(self, config: Config):
        self.config = config
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    
    async def post_jobs_to_channel(self, jobs: List[Dict]) -> bool:
        """Post jobs to Telegram channel"""
        if not jobs:
            logger.info("No jobs to post to Telegram")
            return True
        
        success_count = 0
        total_jobs = len(jobs)
        
        logger.info(f"Posting {total_jobs} jobs to Telegram channel")
        
        try:
            # Group jobs for batch posting
            job_batches = self.group_jobs_for_posting(jobs)
            
            for batch in job_batches:
                try:
                    message = self.format_jobs_message(batch)
                    
                    # Send message to channel
                    await self.bot.send_message(
                        chat_id=self.config.TELEGRAM_CHANNEL_ID,
                        text=message,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    
                    success_count += len(batch)
                    logger.info(f"Posted batch of {len(batch)} jobs to Telegram")
                    
                    # Add delay between batches to avoid rate limiting
                    await asyncio.sleep(2)
                    
                except TelegramError as e:
                    logger.error(f"Failed to post job batch to Telegram: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error posting to Telegram: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in Telegram posting process: {e}")
            return False
        
        logger.info(f"Successfully posted {success_count}/{total_jobs} jobs to Telegram")
        return success_count > 0
    
    def group_jobs_for_posting(self, jobs: List[Dict]) -> List[List[Dict]]:
        """Group jobs into batches for posting"""
        max_jobs_per_message = self.config.MAX_JOBS_PER_POST
        batches = []
        
        # Group by category first
        gov_jobs = [job for job in jobs if job.get('category') == 'government']
        private_jobs = [job for job in jobs if job.get('category') == 'private']
        
        # Create batches for government jobs
        for i in range(0, len(gov_jobs), max_jobs_per_message):
            batch = gov_jobs[i:i + max_jobs_per_message]
            batches.append(batch)
        
        # Create batches for private jobs
        for i in range(0, len(private_jobs), max_jobs_per_message):
            batch = private_jobs[i:i + max_jobs_per_message]
            batches.append(batch)
        
        return batches
    
    def format_jobs_message(self, jobs: List[Dict]) -> str:
        """Format jobs into a Telegram message"""
        if not jobs:
            return ""
        
        # Determine category for header
        categories = [job.get('category', 'government') for job in jobs]
        is_government = 'government' in categories
        is_private = 'private' in categories
        
        if is_government and is_private:
            header = "🔔 <b>Latest Job Opportunities</b> 🔔"
        elif is_government:
            header = "🏛️ <b>Government Job Opportunities</b> 🏛️"
        else:
            header = "🏢 <b>Private Job Opportunities</b> 🏢"
        
        message_parts = [header, ""]
        
        for i, job in enumerate(jobs, 1):
            job_text = self.format_single_job(job, i)
            message_parts.append(job_text)
            message_parts.append("")  # Empty line between jobs
        
        # Add footer
        footer = "📢 <i>Stay updated with latest job notifications!</i>\n" \
                "⚡ <i>Apply soon as positions fill up quickly</i>"
        message_parts.append(footer)
        
        message = "\n".join(message_parts)
        
        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            message = message[:4090] + "..."
        
        return message
    
    def format_single_job(self, job: Dict, index: int) -> str:
        """Format a single job for Telegram message"""
        title = job.get('title', 'Job Opening')
        location = job.get('location', 'India')
        state = job.get('state', '')
        qualification = job.get('qualification', 'As per notification')
        last_date = job.get('last_date', 'Check notification')
        source = job.get('source', 'Job Portal')
        apply_link = job.get('apply_link', '')
        category = job.get('category', 'government')
        
        # Category emoji
        category_emoji = "🏛️" if category == 'government' else "🏢"
        
        # Format location with state
        location_text = location
        if state and state != location:
            location_text = f"{location}, {state}"
        
        job_parts = [
            f"{category_emoji} <b>{index}. {title}</b>",
            f"📍 <b>Location:</b> {location_text}",
            f"🎓 <b>Qualification:</b> {qualification}",
            f"⏰ <b>Last Date:</b> {last_date}",
            f"🔗 <b>Source:</b> {source}"
        ]
        
        # Add apply link if available
        if apply_link:
            job_parts.append(f"👉 <a href='{apply_link}'>Apply Here</a>")
        
        return "\n".join(job_parts)
    
    async def test_bot_connection(self) -> bool:
        """Test if bot can connect and send messages"""
        try:
            # Get bot info
            bot_info = await self.bot.get_me()
            logger.info(f"Bot connected successfully: {bot_info.username}")
            
            # Test sending a message
            test_message = "🤖 Bot connection test successful!"
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHANNEL_ID,
                text=test_message
            )
            
            logger.info("Test message sent successfully")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram bot connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in bot test: {e}")
            return False
    
    async def send_status_update(self, message: str):
        """Send a status update to the channel"""
        try:
            status_message = f"📊 <b>Bot Status Update</b>\n\n{message}"
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHANNEL_ID,
                text=status_message,
                parse_mode='HTML'
            )
            logger.info("Status update sent to Telegram")
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")

def run_telegram_posting(config: Config, jobs: List[Dict]) -> bool:
    """Helper function to run Telegram posting synchronously"""
    async def _post():
        poster = TelegramJobPoster(config)
        return await poster.post_jobs_to_channel(jobs)
    
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_post())
    except Exception as e:
        logger.error(f"Error running Telegram posting: {e}")
        return False
