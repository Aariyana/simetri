"""
Storage manager for job data using JSON files
"""

import json
import logging
import os
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)

class StorageManager:
    """Manage job data storage in JSON files"""
    
    def __init__(self, config: Config):
        self.config = config
        self.jobs_file = config.JOBS_FILE
        self.posted_jobs_file = config.POSTED_JOBS_FILE
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.jobs_file), exist_ok=True)
    
    def load_existing_jobs(self) -> List[Dict]:
        """Load existing jobs from storage"""
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    jobs = json.load(f)
                logger.info(f"Loaded {len(jobs)} existing jobs from storage")
                return jobs
            else:
                logger.info("No existing jobs file found")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding jobs JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading existing jobs: {e}")
            return []
    
    def save_jobs(self, jobs: List[Dict]):
        """Save jobs to storage"""
        try:
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(jobs)} jobs to storage")
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")
    
    def load_posted_jobs(self) -> List[Dict]:
        """Load posted jobs from storage"""
        try:
            if os.path.exists(self.posted_jobs_file):
                with open(self.posted_jobs_file, 'r', encoding='utf-8') as f:
                    jobs = json.load(f)
                logger.info(f"Loaded {len(jobs)} posted jobs from storage")
                return jobs
            else:
                logger.info("No posted jobs file found")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding posted jobs JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading posted jobs: {e}")
            return []
    
    def save_posted_jobs(self, jobs: List[Dict]):
        """Save posted jobs to storage"""
        try:
            with open(self.posted_jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(jobs)} posted jobs to storage")
        except Exception as e:
            logger.error(f"Error saving posted jobs: {e}")
    
    def append_job(self, job: Dict):
        """Append a single job to existing jobs"""
        try:
            existing_jobs = self.load_existing_jobs()
            existing_jobs.append(job)
            self.save_jobs(existing_jobs)
            logger.info("Appended new job to storage")
        except Exception as e:
            logger.error(f"Error appending job: {e}")
    
    def get_jobs_by_state(self, state: str) -> List[Dict]:
        """Get jobs filtered by state"""
        jobs = self.load_existing_jobs()
        state_jobs = [job for job in jobs if job.get('state') == state]
        return state_jobs
    
    def get_jobs_by_category(self, category: str) -> List[Dict]:
        """Get jobs filtered by category"""
        jobs = self.load_existing_jobs()
        category_jobs = [job for job in jobs if job.get('category') == category]
        return category_jobs
    
    def get_jobs_by_source(self, source: str) -> List[Dict]:
        """Get jobs filtered by source"""
        jobs = self.load_existing_jobs()
        source_jobs = [job for job in jobs if job.get('source') == source]
        return source_jobs
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            jobs = self.load_existing_jobs()
            posted_jobs = self.load_posted_jobs()
            
            # Calculate statistics
            total_jobs = len(jobs)
            total_posted = len(posted_jobs)
            
            # Jobs by category
            gov_jobs = len([job for job in jobs if job.get('category') == 'government'])
            private_jobs = len([job for job in jobs if job.get('category') == 'private'])
            
            # Jobs by source
            source_stats = {}
            for job in jobs:
                source = job.get('source', 'Unknown')
                source_stats[source] = source_stats.get(source, 0) + 1
            
            # Jobs by state
            state_stats = {}
            for job in jobs:
                state = job.get('state', 'Unknown')
                state_stats[state] = state_stats.get(state, 0) + 1
            
            stats = {
                'total_jobs': total_jobs,
                'total_posted': total_posted,
                'government_jobs': gov_jobs,
                'private_jobs': private_jobs,
                'jobs_by_source': source_stats,
                'jobs_by_state': state_stats,
                'storage_files': {
                    'jobs_file': os.path.exists(self.jobs_file),
                    'posted_jobs_file': os.path.exists(self.posted_jobs_file)
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating storage stats: {e}")
            return {}
    
    def backup_data(self) -> bool:
        """Create backup of current data"""
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup jobs file
            if os.path.exists(self.jobs_file):
                backup_jobs_file = f"{self.jobs_file}.backup_{timestamp}"
                with open(self.jobs_file, 'r', encoding='utf-8') as src:
                    with open(backup_jobs_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Created backup: {backup_jobs_file}")
            
            # Backup posted jobs file
            if os.path.exists(self.posted_jobs_file):
                backup_posted_file = f"{self.posted_jobs_file}.backup_{timestamp}"
                with open(self.posted_jobs_file, 'r', encoding='utf-8') as src:
                    with open(backup_posted_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Created backup: {backup_posted_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def clear_all_data(self):
        """Clear all stored data (use with caution)"""
        try:
            if os.path.exists(self.jobs_file):
                os.remove(self.jobs_file)
                logger.info("Cleared jobs data")
            
            if os.path.exists(self.posted_jobs_file):
                os.remove(self.posted_jobs_file)
                logger.info("Cleared posted jobs data")
                
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
