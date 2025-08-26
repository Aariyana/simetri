"""
Utility functions for the Indian Job Bot
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class TextUtils:
    """Text processing utilities"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove unwanted characters but keep essential punctuation
        text = re.sub(r'[^\w\s\.\,\:\;\-\(\)\[\]\/\&\@\#]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract Indian phone numbers from text"""
        # Pattern for Indian phone numbers
        phone_patterns = [
            r'\+91[-\s]?\d{10}',  # +91 followed by 10 digits
            r'91[-\s]?\d{10}',    # 91 followed by 10 digits
            r'\b\d{10}\b',        # 10 digits
            r'\b\d{3}[-\s]\d{3}[-\s]\d{4}\b'  # XXX-XXX-XXXX format
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return list(set(phones))
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extract potential dates from text"""
        date_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if isinstance(matches[0], tuple) if matches else False:
                dates.extend([' '.join(match) for match in matches])
            else:
                dates.extend(matches)
        
        return list(set(dates))

class URLUtils:
    """URL processing utilities"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def normalize_url(url: str, base_url: str = None) -> str:
        """Normalize URL and make it absolute"""
        if not url:
            return ""
        
        # If URL is already absolute, return as is
        if url.startswith(('http://', 'https://')):
            return url
        
        # If base URL is provided and URL is relative, make it absolute
        if base_url and url.startswith('/'):
            return urljoin(base_url, url)
        
        return url
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""

class DateUtils:
    """Date processing utilities"""
    
    @staticmethod
    def parse_indian_date(date_str: str) -> Optional[datetime]:
        """Parse Indian date formats"""
        if not date_str:
            return None
        
        date_str = date_str.strip().lower()
        
        # Common Indian date formats
        formats = [
            '%d-%m-%Y',      # 01-12-2023
            '%d/%m/%Y',      # 01/12/2023
            '%d-%m-%y',      # 01-12-23
            '%d/%m/%y',      # 01/12/23
            '%d %B %Y',      # 01 December 2023
            '%d %b %Y',      # 01 Dec 2023
            '%B %d, %Y',     # December 01, 2023
            '%b %d, %Y',     # Dec 01, 2023
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def is_date_expired(date_str: str) -> bool:
        """Check if a date string represents an expired date"""
        parsed_date = DateUtils.parse_indian_date(date_str)
        if not parsed_date:
            return False
        
        return parsed_date < datetime.now()
    
    @staticmethod
    def days_until_date(date_str: str) -> Optional[int]:
        """Calculate days until given date"""
        parsed_date = DateUtils.parse_indian_date(date_str)
        if not parsed_date:
            return None
        
        delta = parsed_date - datetime.now()
        return delta.days

class JobUtils:
    """Job-specific utilities"""
    
    @staticmethod
    def extract_salary_info(text: str) -> str:
        """Extract salary information from job text"""
        salary_patterns = [
            r'salary[:\s]*₹?\s*[\d,]+-?[\d,]*',
            r'pay[:\s]*₹?\s*[\d,]+-?[\d,]*',
            r'₹\s*[\d,]+-?[\d,]*',
            r'rs\.?\s*[\d,]+-?[\d,]*',
            r'\b\d+\s*lpa\b',  # Lakhs per annum
            r'\b\d+\s*k\s*pm\b'  # K per month
        ]
        
        text_lower = text.lower()
        for pattern in salary_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        return ""
    
    @staticmethod
    def extract_experience_required(text: str) -> str:
        """Extract experience requirements from job text"""
        exp_patterns = [
            r'experience[:\s]*\d+-?\d*\s*years?',
            r'exp[:\s]*\d+-?\d*\s*years?',
            r'\d+-?\d*\s*years?\s*experience',
            r'fresher',
            r'no experience',
            r'entry level'
        ]
        
        text_lower = text.lower()
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        return "As per requirements"
    
    @staticmethod
    def categorize_job_level(title: str, description: str) -> str:
        """Categorize job level (entry, mid, senior)"""
        content = (title + " " + description).lower()
        
        # Senior level indicators
        senior_keywords = ['senior', 'lead', 'manager', 'head', 'director', 'chief', 'principal']
        if any(keyword in content for keyword in senior_keywords):
            return "senior"
        
        # Entry level indicators
        entry_keywords = ['fresher', 'trainee', 'intern', 'junior', 'entry', 'graduate']
        if any(keyword in content for keyword in entry_keywords):
            return "entry"
        
        # Default to mid-level
        return "mid"

class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def validate_job_data(job: Dict) -> List[str]:
        """Validate job data and return list of errors"""
        errors = []
        
        required_fields = ['title', 'source']
        for field in required_fields:
            if not job.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate title length
        if job.get('title') and len(job['title']) < 5:
            errors.append("Job title too short")
        
        # Validate URLs
        if job.get('apply_link') and not URLUtils.is_valid_url(job['apply_link']):
            errors.append("Invalid apply link URL")
        
        # Validate category
        if job.get('category') and job['category'] not in ['government', 'private']:
            errors.append("Invalid job category")
        
        return errors
    
    @staticmethod
    def is_spam_job(job: Dict) -> bool:
        """Check if job might be spam"""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        
        # Spam indicators
        spam_keywords = [
            'work from home easy money',
            'earn money online',
            'get rich quick',
            'mlm',
            'pyramid scheme',
            'investment opportunity',
            'guaranteed income'
        ]
        
        content = title + " " + description
        
        for keyword in spam_keywords:
            if keyword in content:
                return True
        
        return False

# Helper functions for backward compatibility
def clean_text(text: str) -> str:
    """Clean text utility function"""
    return TextUtils.clean_text(text)

def is_valid_url(url: str) -> bool:
    """URL validation utility function"""
    return URLUtils.is_valid_url(url)

def validate_job(job: Dict) -> bool:
    """Simple job validation function"""
    errors = ValidationUtils.validate_job_data(job)
    return len(errors) == 0
