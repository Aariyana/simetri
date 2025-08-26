"""
Configuration settings for the Indian Job Bot
"""

import os
from typing import List, Dict

class Config:
    """Configuration class for managing bot settings"""
    
    def __init__(self):
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')
        
        # Blogger Configuration
        self.BLOGGER_API_KEY = os.getenv('BLOGGER_API_KEY', '')
        self.BLOGGER_BLOG_ID = os.getenv('BLOGGER_BLOG_ID', '')
        
        # Scraping Configuration
        self.SCRAPING_INTERVAL = int(os.getenv('SCRAPING_INTERVAL', '3600'))  # 1 hour default
        self.MAX_JOBS_PER_POST = int(os.getenv('MAX_JOBS_PER_POST', '5'))
        self.REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2.0'))  # Delay between requests
        
        # Storage Configuration
        self.DATA_DIR = os.getenv('DATA_DIR', 'data')
        self.JOBS_FILE = os.path.join(self.DATA_DIR, 'jobs.json')
        self.POSTED_JOBS_FILE = os.path.join(self.DATA_DIR, 'posted_jobs.json')
        
        # Indian States for categorization
        self.INDIAN_STATES = [
            'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
            'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
            'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
            'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
            'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
            'West Bengal', 'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Puducherry',
            'Chandigarh', 'Dadra and Nagar Haveli', 'Daman and Diu', 'Lakshadweep',
            'Andaman and Nicobar Islands'
        ]
        
        # Job Categories
        self.JOB_CATEGORIES = {
            'government': ['sarkari', 'government', 'govt', 'public sector', 'psu', 'railway', 'bank', 'ssc', 'upsc'],
            'private': ['private', 'corporate', 'company', 'mnc', 'startup', 'it', 'software']
        }
        
        # Scraping Sources
        self.SCRAPING_SOURCES = {
            'sarkari_result': {
                'url': 'https://www.sarkariresult.com',
                'enabled': True,
                'category': 'government'
            },
            'freshers_world': {
                'url': 'https://www.freshersworld.com',
                'enabled': True,
                'category': 'both'
            },
            'naukri': {
                'url': 'https://www.naukri.com',
                'enabled': True,
                'category': 'private'
            }
        }
        
        # Create data directory if it doesn't exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate required configuration settings"""
        required_fields = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHANNEL_ID'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            print("Please set the following environment variables:")
            for field in missing_fields:
                print(f"  export {field}=your_value_here")
            return False
        
        return True
    
    def get_user_agent(self) -> str:
        """Get a realistic user agent for web scraping"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
"""
Configuration settings for the Indian Job Bot
"""

import os
from typing import List, Dict

class Config:
    """Configuration class for managing bot settings"""
    
    def __init__(self):
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')
        
        # Blogger Configuration
        self.BLOGGER_API_KEY = os.getenv('BLOGGER_API_KEY', '')
        self.BLOGGER_BLOG_ID = os.getenv('BLOGGER_BLOG_ID', '')
        
        # Scraping Configuration
        self.SCRAPING_INTERVAL = int(os.getenv('SCRAPING_INTERVAL', '3600'))  # 1 hour default
        self.MAX_JOBS_PER_POST = int(os.getenv('MAX_JOBS_PER_POST', '5'))
        self.REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2.0'))  # Delay between requests
        
        # Storage Configuration
        self.DATA_DIR = os.getenv('DATA_DIR', 'data')
        self.JOBS_FILE = os.path.join(self.DATA_DIR, 'jobs.json')
        self.POSTED_JOBS_FILE = os.path.join(self.DATA_DIR, 'posted_jobs.json')
        
        # Indian States for categorization
        self.INDIAN_STATES = [
            'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
            'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
            'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
            'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
            'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
            'West Bengal', 'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Puducherry',
            'Chandigarh', 'Dadra and Nagar Haveli', 'Daman and Diu', 'Lakshadweep',
            'Andaman and Nicobar Islands'
        ]
        
        # Job Categories
        self.JOB_CATEGORIES = {
            'government': ['sarkari', 'government', 'govt', 'public sector', 'psu', 'railway', 'bank', 'ssc', 'upsc'],
            'private': ['private', 'corporate', 'company', 'mnc', 'startup', 'it', 'software']
        }
        
        # Scraping Sources
        self.SCRAPING_SOURCES = {
            'sarkari_result': {
                'url': 'https://www.sarkariresult.com',
                'enabled': True,
                'category': 'government'
            },
            'freshers_world': {
                'url': 'https://www.freshersworld.com',
                'enabled': True,
                'category': 'both'
            },
            'naukri': {
                'url': 'https://www.naukri.com',
                'enabled': True,
                'category': 'private'
            }
        }
        
        # Create data directory if it doesn't exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate required configuration settings"""
        required_fields = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHANNEL_ID'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            print("Please set the following environment variables:")
            for field in missing_fields:
                print(f"  export {field}=your_value_here")
            return False
        
        return True
    
    def get_user_agent(self) -> str:
        """Get a realistic user agent for web scraping"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
