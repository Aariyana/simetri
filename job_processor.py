"""
Job processor for handling scraped job data
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set
from hashlib import md5
from config import Config
from storage import StorageManager

logger = logging.getLogger(__name__)

class JobProcessor:
    """Process and manage scraped job data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.storage = StorageManager(config)
    
    def process_jobs(self, scraped_jobs: List[Dict]) -> List[Dict]:
        """Process scraped jobs and return new unique jobs"""
        if not scraped_jobs:
            logger.info("No jobs to process")
            return []
        
        logger.info(f"Processing {len(scraped_jobs)} scraped jobs")
        
        # Load existing jobs to check for duplicates
        existing_jobs = self.storage.load_existing_jobs()
        posted_jobs = self.storage.load_posted_jobs()
        
        # Create sets of job hashes for quick lookup
        existing_hashes = {self.generate_job_hash(job) for job in existing_jobs}
        posted_hashes = {self.generate_job_hash(job) for job in posted_jobs}
        
        new_jobs = []
        duplicate_count = 0
        
        for job in scraped_jobs:
            try:
                # Clean and validate job data
                processed_job = self.clean_and_validate_job(job)
                if not processed_job:
                    continue
                
                # Generate hash for duplicate detection
                job_hash = self.generate_job_hash(processed_job)
                
                # Check if job already exists or has been posted
                if job_hash in existing_hashes or job_hash in posted_hashes:
                    duplicate_count += 1
                    continue
                
                # Add job hash for future duplicate detection
                processed_job['job_hash'] = job_hash
                existing_hashes.add(job_hash)
                
                new_jobs.append(processed_job)
                
            except Exception as e:
                logger.error(f"Error processing job: {e}")
                continue
        
        logger.info(f"Found {len(new_jobs)} new jobs, {duplicate_count} duplicates")
        
        # Save new jobs to storage
        if new_jobs:
            all_jobs = existing_jobs + new_jobs
            self.storage.save_jobs(all_jobs)
        
        return new_jobs
    
    def clean_and_validate_job(self, job: Dict) -> Dict:
        """Clean and validate job data"""
        if not job:
            return None
        
        # Required fields
        required_fields = ['title', 'source']
        for field in required_fields:
            if not job.get(field):
                logger.warning(f"Job missing required field: {field}")
                return None
        
        # Clean text fields
        text_fields = ['title', 'description', 'location', 'qualification', 'last_date']
        for field in text_fields:
            if job.get(field):
                job[field] = self.clean_text(job[field])
        
        # Set default values for missing fields
        defaults = {
            'description': 'Job details not available',
            'location': 'India',
            'state': None,
            'category': 'government',
            'qualification': 'As per notification',
            'last_date': 'Check notification',
            'apply_link': '',
            'scraped_at': datetime.now().isoformat()
        }
        
        for field, default_value in defaults.items():
            if not job.get(field):
                job[field] = default_value
        
        # Validate category
        if job['category'] not in ['government', 'private']:
            job['category'] = 'government'
        
        # Limit field lengths
        job['title'] = job['title'][:200]
        job['description'] = job['description'][:1000]
        job['location'] = job['location'][:100]
        job['qualification'] = job['qualification'][:200]
        job['last_date'] = job['last_date'][:100]
        
        # Add processing timestamp
        job['processed_at'] = datetime.now().isoformat()
        
        return job
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove unwanted characters
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove multiple spaces
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        return text.strip()
    
    def generate_job_hash(self, job: Dict) -> str:
        """Generate a hash for job deduplication"""
        # Use title, location, and source for hash generation
        hash_content = f"{job.get('title', '')}{job.get('location', '')}{job.get('source', '')}"
        hash_content = hash_content.lower().strip()
        return md5(hash_content.encode('utf-8')).hexdigest()
    
    def categorize_jobs_by_state(self, jobs: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize jobs by Indian state"""
        state_jobs = {}
        
        for job in jobs:
            state = job.get('state') or 'Other'
            
            if state not in state_jobs:
                state_jobs[state] = []
            
            state_jobs[state].append(job)
        
        return state_jobs
    
    def categorize_jobs_by_type(self, jobs: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize jobs by government/private type"""
        type_jobs = {
            'government': [],
            'private': []
        }
        
        for job in jobs:
            job_type = job.get('category', 'government')
            if job_type in type_jobs:
                type_jobs[job_type].append(job)
        
        return type_jobs
    
    def get_jobs_for_posting(self, limit: int = None) -> List[Dict]:
        """Get jobs ready for posting"""
        jobs = self.storage.load_existing_jobs()
        posted_jobs = self.storage.load_posted_jobs()
        
        # Create set of posted job hashes
        posted_hashes = {job.get('job_hash') for job in posted_jobs if job.get('job_hash')}
        
        # Filter out already posted jobs
        unposted_jobs = []
        for job in jobs:
            if job.get('job_hash') not in posted_hashes:
                unposted_jobs.append(job)
        
        # Sort by scraped time (newest first)
        unposted_jobs.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
        
        # Apply limit if specified
        if limit:
            unposted_jobs = unposted_jobs[:limit]
        
        logger.info(f"Found {len(unposted_jobs)} jobs ready for posting")
        return unposted_jobs
    
    def mark_jobs_as_posted(self, jobs: List[Dict]):
        """Mark jobs as posted"""
        if not jobs:
            return
        
        posted_jobs = self.storage.load_posted_jobs()
        
        # Add timestamp to jobs
        for job in jobs:
            job['posted_at'] = datetime.now().isoformat()
        
        # Add to posted jobs list
        posted_jobs.extend(jobs)
        
        # Keep only recent posted jobs (last 30 days) to prevent file from growing too large
        cutoff_date = datetime.now() - timedelta(days=30)
        posted_jobs = [
            job for job in posted_jobs 
            if datetime.fromisoformat(job.get('posted_at', datetime.now().isoformat())) > cutoff_date
        ]
        
        self.storage.save_posted_jobs(posted_jobs)
        logger.info(f"Marked {len(jobs)} jobs as posted")
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up old job data"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean up old jobs
        jobs = self.storage.load_existing_jobs()
        recent_jobs = []
        
        for job in jobs:
            scraped_at = job.get('scraped_at')
            if scraped_at:
                try:
                    scraped_date = datetime.fromisoformat(scraped_at)
                    if scraped_date > cutoff_date:
                        recent_jobs.append(job)
                except ValueError:
                    # Keep jobs with invalid dates
                    recent_jobs.append(job)
        
        if len(recent_jobs) < len(jobs):
            self.storage.save_jobs(recent_jobs)
            logger.info(f"Cleaned up {len(jobs) - len(recent_jobs)} old job records")
