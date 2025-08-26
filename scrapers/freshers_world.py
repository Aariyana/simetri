"""
Scraper for FreshersWorld.com - Job portal for fresh graduates
"""

import logging
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin
from .base_scraper import BaseJobScraper

logger = logging.getLogger(__name__)

class FreshersWorldScraper(BaseJobScraper):
    """Scraper for FreshersWorld.com"""
    
    def get_source_name(self) -> str:
        return "FreshersWorld"
    
    def scrape_jobs(self) -> List[Dict]:
        """Scrape jobs from FreshersWorld.com"""
        jobs = []
        base_url = "https://www.freshersworld.com"
        
        try:
            logger.info("Starting FreshersWorld scraping...")
            
            # Try different job listing pages
            job_pages = [
                f"{base_url}/jobs/jobsearch/government-jobs-in-india",
                f"{base_url}/jobs/jobsearch/fresher-jobs-in-india",
                f"{base_url}/latest-jobs"
            ]
            
            for page_url in job_pages:
                try:
                    page_jobs = self.scrape_job_page(page_url)
                    jobs.extend(page_jobs)
                    
                    if len(jobs) >= 15:  # Limit total jobs
                        break
                        
                except Exception as e:
                    logger.error(f"Error scraping FreshersWorld page {page_url}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from FreshersWorld")
            
        except Exception as e:
            logger.error(f"Error scraping FreshersWorld: {e}")
        
        return jobs[:15]  # Return max 15 jobs
    
    def scrape_job_page(self, page_url: str) -> List[Dict]:
        """Scrape jobs from a specific FreshersWorld page"""
        jobs = []
        
        response = self.make_request(page_url)
        if not response:
            return jobs
        
        soup = self.parse_html(response.text)
        
        # Look for job listings - FreshersWorld uses various formats
        job_containers = []
        
        # Try different selectors for job listings
        selectors = [
            '.job-container',
            '.job-item',
            '.jobs-list .job',
            '.job-card',
            '.latest-job',
            'div[class*="job"]'
        ]
        
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                job_containers = containers[:10]  # Max 10 per page
                break
        
        # If no specific containers found, look for links with job-related keywords
        if not job_containers:
            all_links = soup.find_all('a', href=True)
            job_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text().lower()
                
                if any(keyword in href.lower() or keyword in text for keyword in 
                       ['job', 'vacancy', 'recruitment', 'hiring']):
                    if href.startswith('/'):
                        job_links.append(urljoin("https://www.freshersworld.com", href))
                    elif href.startswith('http'):
                        job_links.append(href)
            
            # Process job links
            for job_link in job_links[:5]:  # Limit to 5 links
                try:
                    job_data = self.scrape_job_from_link(job_link)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error processing job link {job_link}: {e}")
        else:
            # Process job containers
            for container in job_containers:
                try:
                    job_data = self.extract_job_from_container(container, page_url)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error processing job container: {e}")
        
        return jobs
    
    def extract_job_from_container(self, container, base_url: str) -> Dict:
        """Extract job information from a job container element"""
        # Extract title
        title = ""
        title_selectors = ['h2', 'h3', '.job-title', '.title', 'a']
        for selector in title_selectors:
            title_elem = container.find(selector)
            if title_elem:
                title = self.clean_text(title_elem.get_text())
                break
        
        # Extract job link
        apply_link = base_url
        link_elem = container.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                apply_link = urljoin("https://www.freshersworld.com", href)
            elif href.startswith('http'):
                apply_link = href
        
        # Extract other details from container text
        container_text = self.clean_text(container.get_text())
        
        # Try to get more details by visiting the job link
        detailed_description = self.get_website_text_content(apply_link)
        if not detailed_description:
            detailed_description = container_text
        
        location = self.extract_location_from_text(detailed_description)
        state = self.extract_state(detailed_description)
        qualification = self.extract_qualification_from_text(detailed_description)
        last_date = self.extract_last_date_from_text(detailed_description)
        category = self.categorize_job(title, detailed_description)
        
        job_data = {
            'title': title or "Job Opening",
            'description': detailed_description[:500] + "..." if len(detailed_description) > 500 else detailed_description,
            'location': location,
            'state': state,
            'category': category,
            'qualification': qualification,
            'last_date': last_date,
            'apply_link': apply_link,
            'source': self.get_source_name(),
            'scraped_at': datetime.now().isoformat()
        }
        
        return job_data
    
    def scrape_job_from_link(self, job_url: str) -> Dict:
        """Scrape job details from a specific job URL"""
        description = self.get_website_text_content(job_url)
        if not description:
            return None
        
        # Extract title from description or URL
        lines = description.split('\n')
        title = self.clean_text(lines[0]) if lines else "Job Opening"
        
        location = self.extract_location_from_text(description)
        state = self.extract_state(description)
        qualification = self.extract_qualification_from_text(description)
        last_date = self.extract_last_date_from_text(description)
        category = self.categorize_job(title, description)
        
        job_data = {
            'title': title,
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
        """Extract location from job text"""
        location_patterns = ['location:', 'city:', 'place:', 'venue:']
        text_lower = text.lower()
        
        for pattern in location_patterns:
            if pattern in text_lower:
                start_idx = text_lower.find(pattern) + len(pattern)
                location_text = text[start_idx:start_idx+100].split('\n')[0]
                return self.clean_text(location_text)
        
        # Look for state names
        for state in self.config.INDIAN_STATES:
            if state.lower() in text_lower:
                return state
        
        return "India"
    
    def extract_qualification_from_text(self, text: str) -> str:
        """Extract qualification from job text"""
        qual_patterns = ['qualification:', 'education:', 'eligibility:', 'degree:']
        text_lower = text.lower()
        
        for pattern in qual_patterns:
            if pattern in text_lower:
                start_idx = text_lower.find(pattern) + len(pattern)
                qual_text = text[start_idx:start_idx+150].split('\n')[0]
                return self.clean_text(qual_text)
        
        # Look for common qualification terms
        qual_terms = ['graduate', 'diploma', 'degree', 'certification', 'experience']
        for term in qual_terms:
            if term in text_lower:
                return f"Candidates with relevant {term}"
        
        return "As per job requirements"
    
    def extract_last_date_from_text(self, text: str) -> str:
        """Extract application deadline from job text"""
        date_patterns = ['last date:', 'deadline:', 'apply by:', 'closing date:']
        text_lower = text.lower()
        
        for pattern in date_patterns:
            if pattern in text_lower:
                start_idx = text_lower.find(pattern) + len(pattern)
                date_text = text[start_idx:start_idx+100].split('\n')[0]
                return self.clean_text(date_text)
        
        return "Check job details"
