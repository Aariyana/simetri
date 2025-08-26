"""
Blogger API client for posting jobs to Blogger site
"""

import logging
from typing import List, Dict
from datetime import datetime
import json
import requests
from config import Config

logger = logging.getLogger(__name__)

class BloggerJobPoster:
    """Handle Blogger API operations for job posting"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.BLOGGER_API_KEY
        self.blog_id = config.BLOGGER_BLOG_ID
        self.base_url = "https://www.googleapis.com/blogger/v3"
    
    def post_jobs_to_blogger(self, jobs: List[Dict]) -> bool:
        """Post jobs to Blogger site"""
        if not self.api_key or not self.blog_id:
            logger.warning("Blogger API key or Blog ID not configured. Skipping Blogger posting.")
            return True
        
        if not jobs:
            logger.info("No jobs to post to Blogger")
            return True
        
        success_count = 0
        total_jobs = len(jobs)
        
        logger.info(f"Posting {total_jobs} jobs to Blogger")
        
        try:
            # Group jobs by category for separate posts
            gov_jobs = [job for job in jobs if job.get('category') == 'government']
            private_jobs = [job for job in jobs if job.get('category') == 'private']
            
            # Post government jobs
            if gov_jobs:
                if self.create_blog_post(gov_jobs, 'government'):
                    success_count += len(gov_jobs)
            
            # Post private jobs
            if private_jobs:
                if self.create_blog_post(private_jobs, 'private'):
                    success_count += len(private_jobs)
            
        except Exception as e:
            logger.error(f"Error in Blogger posting process: {e}")
            return False
        
        logger.info(f"Successfully posted {success_count}/{total_jobs} jobs to Blogger")
        return success_count > 0
    
    def create_blog_post(self, jobs: List[Dict], category: str) -> bool:
        """Create a blog post for jobs"""
        try:
            title = self.generate_post_title(jobs, category)
            content = self.generate_post_content(jobs, category)
            labels = self.generate_post_labels(jobs, category)
            
            post_data = {
                "title": title,
                "content": content,
                "labels": labels
            }
            
            url = f"{self.base_url}/blogs/{self.blog_id}/posts"
            params = {"key": self.api_key}
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data=json.dumps(post_data),
                timeout=30
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully created Blogger post for {category} jobs")
                return True
            else:
                logger.error(f"Failed to create Blogger post: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Request error posting to Blogger: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting to Blogger: {e}")
            return False
    
    def generate_post_title(self, jobs: List[Dict], category: str) -> str:
        """Generate title for the blog post"""
        date_str = datetime.now().strftime("%B %d, %Y")
        
        if category == 'government':
            title = f"Latest Government Job Opportunities - {date_str}"
        else:
            title = f"Latest Private Job Opportunities - {date_str}"
        
        # Add state information if jobs are from specific states
        states = set()
        for job in jobs:
            if job.get('state'):
                states.add(job['state'])
        
        if len(states) == 1:
            state = list(states)[0]
            title = f"{title} | {state} Jobs"
        elif len(states) <= 3:
            states_str = ", ".join(list(states))
            title = f"{title} | {states_str}"
        
        return title
    
    def generate_post_content(self, jobs: List[Dict], category: str) -> str:
        """Generate HTML content for the blog post"""
        date_str = datetime.now().strftime("%B %d, %Y")
        
        # Header
        if category == 'government':
            header = f"""
            <h2>🏛️ Latest Government Job Opportunities - {date_str}</h2>
            <p>Find the latest government job openings across India. Apply soon as positions fill up quickly!</p>
            """
        else:
            header = f"""
            <h2>🏢 Latest Private Job Opportunities - {date_str}</h2>
            <p>Discover exciting career opportunities in the private sector across India.</p>
            """
        
        # Job listings
        job_html_parts = [header]
        
        for i, job in enumerate(jobs, 1):
            job_html = self.format_job_for_html(job, i)
            job_html_parts.append(job_html)
        
        # Footer
        footer = """
        <hr>
        <h3>📢 How to Apply</h3>
        <ul>
            <li>Click on the "Apply Here" links for each job</li>
            <li>Read the complete job notification carefully</li>
            <li>Check eligibility criteria before applying</li>
            <li>Apply before the last date</li>
        </ul>
        
        <h3>🔔 Stay Updated</h3>
        <p>Subscribe to our blog and join our Telegram channel for daily job updates!</p>
        
        <p><em>Disclaimer: We are not responsible for any changes in job details. Please verify information from official sources.</em></p>
        """
        
        job_html_parts.append(footer)
        
        return "\n".join(job_html_parts)
    
    def format_job_for_html(self, job: Dict, index: int) -> str:
        """Format a single job for HTML content"""
        title = job.get('title', 'Job Opening')
        location = job.get('location', 'India')
        state = job.get('state', '')
        qualification = job.get('qualification', 'As per notification')
        last_date = job.get('last_date', 'Check notification')
        source = job.get('source', 'Job Portal')
        apply_link = job.get('apply_link', '')
        description = job.get('description', 'Job details not available')
        category = job.get('category', 'government')
        
        # Category styling
        category_badge = '<span style="background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Government</span>' if category == 'government' else '<span style="background-color: #2196F3; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Private</span>'
        
        # Format location
        location_text = location
        if state and state != location:
            location_text = f"{location}, {state}"
        
        job_html = f"""
        <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px; background-color: #f9f9f9;">
            <h3>{index}. {title} {category_badge}</h3>
            
            <div style="margin: 10px 0;">
                <p><strong>📍 Location:</strong> {location_text}</p>
                <p><strong>🎓 Qualification:</strong> {qualification}</p>
                <p><strong>⏰ Last Date:</strong> {last_date}</p>
                <p><strong>🔗 Source:</strong> {source}</p>
            </div>
            
            <div style="margin: 10px 0;">
                <p><strong>📄 Job Details:</strong></p>
                <p style="color: #666; font-size: 14px;">{description[:300]}{'...' if len(description) > 300 else ''}</p>
            </div>
        """
        
        if apply_link:
            job_html += f"""
            <div style="margin-top: 15px;">
                <a href="{apply_link}" target="_blank" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">👉 Apply Here</a>
            </div>
            """
        
        job_html += "</div>"
        
        return job_html
    
    def generate_post_labels(self, jobs: List[Dict], category: str) -> List[str]:
        """Generate labels/tags for the blog post"""
        labels = ["Jobs", "Career", "India"]
        
        if category == 'government':
            labels.extend(["Government Jobs", "Sarkari Jobs", "Public Sector"])
        else:
            labels.extend(["Private Jobs", "Corporate Jobs", "IT Jobs"])
        
        # Add state labels
        states = set()
        for job in jobs:
            if job.get('state'):
                states.add(job['state'])
        
        # Add up to 3 state labels
        for state in list(states)[:3]:
            labels.append(f"{state} Jobs")
        
        return labels
    
    def test_blogger_connection(self) -> bool:
        """Test Blogger API connection"""
        if not self.api_key or not self.blog_id:
            logger.warning("Blogger API credentials not configured")
            return False
        
        try:
            url = f"{self.base_url}/blogs/{self.blog_id}"
            params = {"key": self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                blog_info = response.json()
                logger.info(f"Blogger connection successful: {blog_info.get('name', 'Blog')}")
                return True
            else:
                logger.error(f"Blogger connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Blogger connection: {e}")
            return False
