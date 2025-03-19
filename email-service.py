import os
import smtplib
import logging
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("arbitrage-bot.email")

# Email configuration from environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "")

def send_email(subject, body):
    """Send an email with the given subject and body"""
    logger.info(f"Sending email: {subject}")
    
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        logger.error("Email configuration is missing. Please set SENDER_EMAIL, SENDER_PASSWORD, and RECEIVER_EMAIL environment variables.")
        return False
    
    try:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
            
        logger.info("Email sent successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}", exc_info=True)
        return False

def send_test_email():
    """Send a test email when the bot first starts"""
    subject = "Sports Arbitrage Bot Active"
    body = """
Hello,

Your Sports Arbitrage Bot is now active and running. The bot will monitor Bet365, BetMGM, and Stake for arbitrage opportunities in Canadian sports markets.

You will receive notifications by email when arbitrage opportunities are found.

Details:
- Bot started at: {time}
- Monitoring: Bet365, BetMGM, Stake
- Region: Canada
- Check frequency: Every {interval} minutes
- Heartbeat frequency: Every {heartbeat} minutes

This is an automated message from your Sports Arbitrage Bot.
    """.format(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        interval=os.environ.get("SCRAPE_INTERVAL", 2),
        heartbeat=os.environ.get("HEARTBEAT_INTERVAL", 3)
    )
    
    return send_email(subject, body)
