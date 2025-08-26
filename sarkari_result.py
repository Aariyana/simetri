"""
Scraper for SarkariResult.com - Government job portal
"""

import logging
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin, urlparse
from .base_scraper import BaseJobScraper

logger = logging.getLogger(__name__)

class SarkariResultScraper(BaseJobScraper):
    """Scraper for SarkariResult.com"""
    
    def get_source_name(self) -> str:
        return "SarkariResult"
    
    def scrape_jobs(self) -> List[Dict]:
        """Scrape jobs from SarkariResult.com"""
        jobs = []
        base_url = "https://www.sarkariresult.com"
        
        try:
            logger.info("Starting SarkariResult scraping...")
            
            # Get the main page
            response = self.make_request(base_url)
            if not response:
                return jobs
            
            soup = self.parse_html(response.text)
            
            # Find job links - SarkariResult typically has job listings in specific sections
            job_links = []
            
            # Look for recent job listings
            recent_jobs_section = soup.find('div', class_='newresult') or soup.find('div', id='newresult')
            if recent_jobs_section:
                links = recent_jobs_section.find_all('a', href=True)
                for link in links[:10]:  # Limit to 10 most recent jobs
                    href = link['href']
                    if href.startswith('/'):
                        job_links.append(urljoin(base_url, href))
                    elif href.startswith('http'):
                        job_links.append(href)
            
            # Also look for job listings in table format
            tables = soup.find_all('table')
            for table in tables:
                links = table.find_all('a', href=True)
                for link in links[:5]:  # Limit per table
                    href = link['href']
                    if href.startswith('/'):
                        job_links.append(urljoin(base_url, href))
            
            # Remove duplicates
            job_links = list(set(job_links))[:15]  # Process max 15 jobs
            
            logger.info(f"Found {len(job_links)} job links on SarkariResult")
            
            # Process each job link
            for job_url in job_links:
                try:
                    job_data = self.scrape_job_details(job_url)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error scraping job from {job_url}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from SarkariResult")
            
        except Exception as e:
            logger.error(f"Error scraping SarkariResult: {e}")
        
        return jobs
    
    def scrape_job_details(self, job_url: str) -> Dict:
        """Scrape details from a specific job page"""
        response = self.make_request(job_url)
        if not response:
            return None
        
        soup = self.parse_html(response.text)
        
        # Extract job title
        title = ""
        title_selectors = ['h1', '.post-title', '.entry-title', 'title']
        for selector in title_selectors:
            title_elem = soup.find(selector)
            if title_elem:
                title = self.clean_text(title_elem.get_text())
                break
        
        if not title:
            # Try to extract from URL or page content
            content_text = self.get_website_text_content(job_url)
            lines = content_text.split('\n')
            if lines:
                title = self.clean_text(lines[0])
        
        # Extract description from page content
        description = self.get_website_text_content(job_url)
        if not description:
            # Fallback to basic text extraction
            description = self.clean_text(soup.get_text())
        
        # Extract key information from description
        location = self.extract_location_from_text(description)
        state = self.extract_state(description)
        qualification = self.extract_qualification_from_text(description)
        last_date = self.extract_last_date_from_text(description)
        
        # Categorize job (SarkariResult is primarily government jobs)
        category = 'government'
        
        job_data = {
            'title': title or "Government Job Opening",
            'description': description[:500] + "..." if len(description) > 500 else description,
            'location': location,
            'state': state,
            'category': category,
            'qualification': qualification,
            'last_date': last_date,
            'apply_link': job_url,
            'source': self.get_source_name(),
            'scraped_at': datetime.now().isoformat()
        }
        
        return job_data
    
    def extract_location_from_text(self, text: str) -> str:
        """Extract location information from text"""
        location_keywords = ['location', 'place', 'venue', 'city', 'district']
        lines = text.lower().split('\n')
        
        for line in lines:
            for keyword in location_keywords:
                if keyword in line and ':' in line:
                    location = line.split(':')[1].strip()
                    return self.clean_text(location)
        
        # Try to find state names in text as location
        for state in self.config.INDIAN_STATES:
            if state.lower() in text.lower():
                return state
        
        return "India"
    
    def extract_qualification_from_text(self, text: str) -> str:
        """Extract qualification requirements from text"""
        qual_keywords = ['qualification', 'eligibility', 'education', 'degree', 'diploma']
        lines = text.lower().split('\n')
        
        for line in lines:
            for keyword in qual_keywords:
                if keyword in line:
                    # Try to extract the line or next few words
                    if ':' in line:
                        qual = line.split(':')[1].strip()
                        return self.clean_text(qual)[:100]  # Limit length
                    else:
                        return self.clean_text(line)[:100]
        
        return "As per notification"
    
    def extract_last_date_from_text(self, text: str) -> str:
        """Extract application last date from text"""
        date_keywords = ['last date', 'closing date', 'deadline', 'apply before', 'due date']
        lines = text.lower().split('\n')
        
        for line in lines:
            for keyword in date_keywords:
                if keyword in line:
                    if ':' in line:
                        date = line.split(':')[1].strip()
                        return self.clean_text(date)[:50]
                    else:
                        return self.clean_text(line)[:50]
        
        return "Check notification"
