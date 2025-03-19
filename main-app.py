import os
import time
import schedule
import threading
import logging
from flask import Flask
from datetime import datetime
from scrapers.bet365_scraper import scrape_odds as scrape_bet365
from scrapers.betmgm_scraper import scrape_odds as scrape_betmgm
from scrapers.stake_scraper import scrape_odds as scrape_stake
from arbitrage_finder import find_arbitrage_opportunities
from email_service import send_email, send_test_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("arbitrage_bot.log"), logging.StreamHandler()]
)

logger = logging.getLogger("arbitrage-bot")

# Initialize Flask app for the server
app = Flask(__name__)

# Global variables
last_heartbeat = datetime.now()
is_first_run = True

@app.route('/')
def home():
    """Health check endpoint for Render"""
    global last_heartbeat
    time_since_last_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
    return {
        "status": "active",
        "last_heartbeat": last_heartbeat.isoformat(),
        "seconds_since_heartbeat": time_since_last_heartbeat,
        "version": "1.0.0"
    }

def heartbeat():
    """Updates the last heartbeat time"""
    global last_heartbeat
    last_heartbeat = datetime.now()
    logger.info("Heartbeat sent at %s", last_heartbeat.isoformat())

def run_arbitrage_check():
    """Main function to check for arbitrage opportunities across bookmakers"""
    global is_first_run
    logger.info("Starting arbitrage check")
    
    try:
        # Send test email on first run
        if is_first_run:
            logger.info("First run detected, sending test email")
            send_test_email()
            is_first_run = False
        
        # Scrape odds from all bookmakers
        bet365_odds = scrape_bet365()
        betmgm_odds = scrape_betmgm()
        stake_odds = scrape_stake()
        
        # Find arbitrage opportunities
        opportunities = find_arbitrage_opportunities(bet365_odds, betmgm_odds, stake_odds)
        
        # Send email if opportunities found
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities!")
            for opp in opportunities:
                send_email(
                    subject=f"Arbitrage Opportunity: {opp['profit_percentage']:.2f}% profit",
                    body=format_opportunity_email(opp)
                )
        else:
            logger.info("No arbitrage opportunities found in this run")
            
    except Exception as e:
        logger.error(f"Error in arbitrage check: {str(e)}", exc_info=True)
        send_email(
            subject="ERROR: Sports Arbitrage Bot Needs Attention",
            body=f"The bot encountered an error: {str(e)}\n\nPlease check the logs and fix the issue."
        )

def format_opportunity_email(opportunity):
    """Format the arbitrage opportunity details for email"""
    return f"""Arbitrage Opportunity Found!

Profit Percentage: {opportunity['profit_percentage']:.2f}%

Event: {opportunity['event']}
Sport: {opportunity['sport']}
Market: {opportunity['market']}

Bet Details:
1. {opportunity['bet1']['bookmaker']} - {opportunity['bet1']['selection']} @ {opportunity['bet1']['odds']} 
   Stake: ${opportunity['bet1']['stake']:.2f} ({opportunity['bet1']['stake_percentage']:.1f}% of total)

2. {opportunity['bet2']['bookmaker']} - {opportunity['bet2']['selection']} @ {opportunity['bet2']['odds']}
   Stake: ${opportunity['bet2']['stake']:.2f} ({opportunity['bet2']['stake_percentage']:.1f}% of total)

Total Stake: ${opportunity['total_stake']:.2f}
Expected Return: ${opportunity['expected_return']:.2f}
Expected Profit: ${opportunity['expected_profit']:.2f}

Time Found: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Good luck!
"""

def schedule_jobs():
    """Schedule the jobs for the bot"""
    # Get check interval from environment or use default
    check_interval = int(os.environ.get("SCRAPE_INTERVAL", 2))
    heartbeat_interval = int(os.environ.get("HEARTBEAT_INTERVAL", 3))
    
    schedule.every(check_interval).minutes.do(run_arbitrage_check)
    schedule.every(heartbeat_interval).minutes.do(heartbeat)
    
    # Run immediately at startup
    run_arbitrage_check()
    heartbeat()
    
    # Keep running the scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Start the scheduling in a separate thread
    scheduler_thread = threading.Thread(target=schedule_jobs)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the Flask app
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
