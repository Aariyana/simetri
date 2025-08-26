"""
Scraper for Naukri.com - Leading job portal in India
"""

import logging
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin
from .base_scraper import BaseJobScraper

logger = logging.getLogger(__name__)

class NaukriScraper(BaseJobScraper):
    """Scraper for Naukri.com"""
    
    def get_source_name(self) -> str:
        return "Naukri"
    
    def scrape_jobs(self) -> List[Dict]:
        """Scrape jobs from Naukri.com"""
        jobs = []
        base_url = "https://www.naukri.com"
        
        try:
            logger.info("Starting Naukri scraping...")
            
            # Search for various job types
            search_queries = [
                "government+jobs",
                "private+jobs",
                "fresher+jobs",
                "latest+jobs"
            ]
            
            for query in search_queries:
                try:
                    search_url = f"{base_url}/jobs-in-india?k={query}"
                    page_jobs = self.scrape_search_results(search_url)
                    jobs.extend(page_jobs)
                    
                    if len(jobs) >= 15:  # Limit total jobs
                        break
                        
                except Exception as e:
                    logger.error(f"Error scraping Naukri search for {query}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Naukri")
            
        except Exception as e:
            logger.error(f"Error scraping Naukri: {e}")
        
        return jobs[:15]  # Return max 15 jobs
    
    def scrape_search_results(self, search_url: str) -> List[Dict]:
        """Scrape jobs from Naukri search results"""
        jobs = []
        
        response = self.make_request(search_url)
        if not response:
            return jobs
        
        soup = self.parse_html(response.text)
        
        # Look for job result containers
        job_containers = []
        
        # Try different selectors that Naukri might use
        selectors = [
            '.jobTuple',
            '.job-tuple',
            '.srp-jobtuple-wrapper',
            '.job-result',
            'div[class*="job"]',
            '.job-card'
        ]
        
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                job_containers = containers[:8]  # Max 8 jobs per search
                break
        
        # If no specific containers found, try generic approach
        if not job_containers:
            # Look for links that might be job links
            all_links = soup.find_all('a', href=True)
            job_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text().lower()
                
                # Filter for job-related links
                if ('job-detail' in href or 'jobs/' in href or 
                    any(keyword in text for keyword in ['apply', 'job', 'vacancy'])):
                    
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    job_links.append(full_url)
            
            # Process job links
            for job_link in job_links[:5]:  # Limit to 5 links
                try:
                    job_data = self.scrape_job_from_url(job_link)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error processing job link {job_link}: {e}")
        else:
            # Process job containers
            for container in job_containers:
                try:
                    job_data = self.extract_job_from_container(container)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error processing job container: {e}")
        
        return jobs
    
    def extract_job_from_container(self, container) -> Dict:
        """Extract job information from a job container element"""
        # Extract title
        title = ""
        title_selectors = ['.title', '.jobTitle', 'h2', 'h3', 'a[title]']
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title = self.clean_text(title_elem.get_text())
                break
        
        # Extract company
        company = ""
        company_selectors = ['.company', '.companyName', '.org']
        for selector in company_selectors:
            company_elem = container.select_one(selector)
            if company_elem:
                company = self.clean_text(company_elem.get_text())
                break
        
        # Extract location
        location = ""
        location_selectors = ['.location', '.locationsContainer', '.job-location']
        for selector in location_selectors:
            location_elem = container.select_one(selector)
            if location_elem:
                location = self.clean_text(location_elem.get_text())
                break
        
        # Extract job link
        apply_link = "https://www.naukri.com"
        link_elem = container.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                apply_link = urljoin("https://www.naukri.com", href)
            elif href.startswith('http'):
                apply_link = href
        
        # Get detailed description by visiting job page
        detailed_description = self.get_website_text_content(apply_link)
        if not detailed_description:
            # Fallback to container text
            detailed_description = self.clean_text(container.get_text())
        
        # Add company info to description
        if company:
            detailed_description = f"Company: {company}\n\n{detailed_description}"
        
        state = self.extract_state(location + " " + detailed_description)
        qualification = self.extract_qualification_from_text(detailed_description)
        last_date = self.extract_last_date_from_text(detailed_description)
        category = self.categorize_job(title, detailed_description)
        
        job_data = {
            'title': title or "Job Opening",
            'description': detailed_description[:500] + "..." if len(detailed_description) > 500 else detailed_description,
            'location': location or "India",
            'state': state,
            'category': category,
            'qualification': qualification,
            'last_date': last_date,
            'apply_link': apply_link,
            'source': self.get_source_name(),
            'scraped_at': datetime.now().isoformat()
        }
        
        return job_data
    
    def scrape_job_from_url(self, job_url: str) -> Dict:
        """Scrape job details from a specific Naukri job URL"""
        description = self.get_website_text_content(job_url)
        if not description:
            return None
        
        # Extract title from the first line or URL
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
        """Extract location from job description"""
        # Look for location patterns
        location_keywords = ['location', 'based in', 'posted in', 'city']
        text_lower = text.lower()
        
        for keyword in location_keywords:
            if keyword in text_lower:
                # Try to extract location after the keyword
                idx = text_lower.find(keyword)
                location_part = text[idx:idx+100]
                
                # Look for state names in this part
                for state in self.config.INDIAN_STATES:
                    if state.lower() in location_part.lower():
                        return state
        
        # Fallback: look for any state name in the entire text
        for state in self.config.INDIAN_STATES:
            if state.lower() in text_lower:
                return state
        
        return "India"
    
    def extract_qualification_from_text(self, text: str) -> str:
        """Extract qualification requirements from job description"""
        qual_keywords = ['qualification', 'education', 'degree', 'experience', 'skills required']
        text_lower = text.lower()
        
        for keyword in qual_keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                qual_part = text[idx:idx+200].split('\n')[0]
                return self.clean_text(qual_part)
        
        # Look for common degree mentions
        degrees = ['bachelor', 'master', 'diploma', 'graduate', 'certification']
        for degree in degrees:
            if degree in text_lower:
                return f"Candidates with {degree} or equivalent"
        
        return "As mentioned in job description"
    
    def extract_last_date_from_text(self, text: str) -> str:
        """Extract application deadline from job description"""
        date_keywords = ['last date', 'apply by', 'deadline', 'closing date', 'expires on']
        text_lower = text.lower()
        
        for keyword in date_keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                date_part = text[idx:idx+100].split('\n')[0]
                return self.clean_text(date_part)
        
        return "Apply as soon as possible"
