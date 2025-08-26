"""
Flask web application for bot monitoring and control
"""

from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime
from config import Config
from storage import StorageManager
from scheduler import JobScheduler
import os

logger = logging.getLogger(__name__)

app = Flask(__name__)
config = Config()
storage = StorageManager(config)

# Global scheduler instance
scheduler_instance = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    try:
        stats = storage.get_storage_stats()
        
        # Add scheduler status if available
        if scheduler_instance:
            scheduler_stats = scheduler_instance.get_scheduler_status()
            stats.update(scheduler_stats)
        
        # Add system info
        stats['system'] = {
            'current_time': datetime.now().isoformat(),
            'log_file_exists': os.path.exists('bot.log'),
            'data_directory': config.DATA_DIR
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs')
def api_jobs():
    """API endpoint for job listings"""
    try:
        # Get query parameters
        category = request.args.get('category', 'all')
        state = request.args.get('state', 'all')
        source = request.args.get('source', 'all')
        limit = int(request.args.get('limit', '50'))
        
        # Load jobs
        jobs = storage.load_existing_jobs()
        
        # Apply filters
        if category != 'all':
            jobs = [job for job in jobs if job.get('category') == category]
        
        if state != 'all':
            jobs = [job for job in jobs if job.get('state') == state]
        
        if source != 'all':
            jobs = [job for job in jobs if job.get('source') == source]
        
        # Sort by scraped date (newest first)
        jobs.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
        
        # Apply limit
        jobs = jobs[:limit]
        
        return jsonify({
            'jobs': jobs,
            'total_count': len(jobs),
            'filters_applied': {
                'category': category,
                'state': state,
                'source': source,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/posted-jobs')
def api_posted_jobs():
    """API endpoint for posted jobs"""
    try:
        posted_jobs = storage.load_posted_jobs()
        
        # Sort by posted date (newest first)
        posted_jobs.sort(key=lambda x: x.get('posted_at', ''), reverse=True)
        
        # Apply limit
        limit = int(request.args.get('limit', '50'))
        posted_jobs = posted_jobs[:limit]
        
        return jsonify({
            'posted_jobs': posted_jobs,
            'total_count': len(posted_jobs)
        })
        
    except Exception as e:
        logger.error(f"Error getting posted jobs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """API endpoint for application logs"""
    try:
        if not os.path.exists('bot.log'):
            return jsonify({'logs': [], 'message': 'No log file found'})
        
        # Read last 100 lines of log file
        with open('bot.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get last N lines
        limit = int(request.args.get('limit', '100'))
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        return jsonify({
            'logs': [line.strip() for line in recent_lines],
            'total_lines': len(lines)
        })
        
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config')
def api_config():
    """API endpoint for configuration info"""
    try:
        config_info = {
            'telegram_configured': bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHANNEL_ID),
            'blogger_configured': bool(config.BLOGGER_API_KEY and config.BLOGGER_BLOG_ID),
            'scraping_interval': config.SCRAPING_INTERVAL,
            'max_jobs_per_post': config.MAX_JOBS_PER_POST,
            'request_delay': config.REQUEST_DELAY,
            'enabled_sources': {
                name: source['enabled'] 
                for name, source in config.SCRAPING_SOURCES.items()
            },
            'data_directory': config.DATA_DIR
        }
        
        return jsonify(config_info)
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connections')
def api_test_connections():
    """API endpoint to test external connections"""
    try:
        results = {}
        
        # Test Telegram connection
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHANNEL_ID:
            try:
                from telegram_bot import TelegramJobPoster
                import asyncio
                
                poster = TelegramJobPoster(config)
                
                async def test_telegram():
                    return await poster.test_bot_connection()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results['telegram'] = loop.run_until_complete(test_telegram())
                
            except Exception as e:
                results['telegram'] = False
                logger.error(f"Telegram test failed: {e}")
        else:
            results['telegram'] = False
        
        # Test Blogger connection
        if config.BLOGGER_API_KEY and config.BLOGGER_BLOG_ID:
            try:
                from blogger_client import BloggerJobPoster
                blogger = BloggerJobPoster(config)
                results['blogger'] = blogger.test_blogger_connection()
            except Exception as e:
                results['blogger'] = False
                logger.error(f"Blogger test failed: {e}")
        else:
            results['blogger'] = False
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error testing connections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual-scrape', methods=['POST'])
def api_manual_scrape():
    """API endpoint to trigger manual scraping"""
    try:
        if not scheduler_instance:
            return jsonify({'error': 'Scheduler not initialized'}), 400
        
        # Trigger scraping job in background
        import threading
        threading.Thread(target=scheduler_instance.run_scraping_job, daemon=True).start()
        
        return jsonify({'message': 'Manual scraping started'})
        
    except Exception as e:
        logger.error(f"Error starting manual scrape: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup-data', methods=['POST'])
def api_backup_data():
    """API endpoint to create data backup"""
    try:
        success = storage.backup_data()
        
        if success:
            return jsonify({'message': 'Backup created successfully'})
        else:
            return jsonify({'error': 'Backup creation failed'}), 500
            
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

def set_scheduler(scheduler):
    """Set the scheduler instance for the web app"""
    global scheduler_instance
    scheduler_instance = scheduler

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
