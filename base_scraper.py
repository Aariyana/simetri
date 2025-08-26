"""
Base scraper class for job websites
"""

import requests
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import trafilatura
from config import Config

logger = logging.getLogger(__name__)

class BaseJobScraper(ABC):
    """Abstract base class for job scrapers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_website_text_content(self, url: str) -> str:
        """
        Extract main text content from a website using trafilatura
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            text = trafilatura.extract(downloaded)
            return text or ""
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""
    
    def make_request(self, url: str, delay: bool = True) -> Optional[requests.Response]:
        """Make HTTP request with error handling and rate limiting"""
        try:
            if delay:
                time.sleep(self.config.REQUEST_DELAY)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common unwanted characters
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        return text.strip()
    
    def extract_state(self, text: str) -> Optional[str]:
        """Extract Indian state from job text"""
        text_lower = text.lower()
        
        for state in self.config.INDIAN_STATES:
            if state.lower() in text_lower:
                return state
        
        return None
    
    def categorize_job(self, title: str, description: str) -> str:
        """Categorize job as government or private"""
        content = (title + " " + description).lower()
        
        # Check for government keywords
        for keyword in self.config.JOB_CATEGORIES['government']:
            if keyword in content:
                return 'government'
        
        # Check for private keywords
        for keyword in self.config.JOB_CATEGORIES['private']:
            if keyword in content:
                return 'private'
        
        # Default to government if uncertain (since we're focused on gov jobs)
        return 'government'
    
    @abstractmethod
    def scrape_jobs(self) -> List[Dict]:
        """
        Abstract method to scrape jobs from the specific website
        Should return a list of job dictionaries with the following structure:
        {
            'title': str,
            'description': str,
            'location': str,
            'state': str,
            'category': str,  # 'government' or 'private'
            'qualification': str,
            'last_date': str,
            'apply_link': str,
            'source': str,
            'scraped_at': str
        }
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of the job source"""
        pass
