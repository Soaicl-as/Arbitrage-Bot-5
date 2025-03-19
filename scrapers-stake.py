import logging
import requests
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger("arbitrage-bot.stake")

def initialize_driver():
    """Initialize headless Chrome driver for Selenium"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {str(e)}")
        raise

def scrape_odds():
    """Scrape odds from Stake for Canadian region"""
    logger.info("Starting Stake scraping")
    sports_to_scrape = [
        "soccer", "ice-hockey", "basketball", "baseball", 
        "tennis", "american-football", "boxing"
    ]
    
    all_odds = {}
    
    try:
        driver = initialize_driver()
        
        for sport in sports_to_scrape:
            logger.info(f"Scraping {sport} from Stake")
            sport_odds = scrape_sport(driver, sport)
            all_odds[sport] = sport_odds
            
            # Random delay between sport scrapes to avoid detection
            time.sleep(random.uniform(1, 3))
        
        driver.quit()
        logger.info(f"Completed Stake scraping, found odds for {len(all_odds)} sports")
        return all_odds
        
    except Exception as e:
        logger.error(f"Error scraping Stake: {str(e)}", exc_info=True)
        if 'driver' in locals():
            driver.quit()
        return {}

def scrape_sport(driver, sport):
    """Scrape a specific sport from Stake"""
    # This is a sample URL structure - you'll need to adjust for actual Stake URLs
    url = f"https://stake.com/sports/{sport}/canada"
    
    try:
        driver.get(url)
        
        # Wait for the odds to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".events-list"))
        )
        
        # Give the page a little more time to fully load
        time.sleep(2)
        
        # Extract events and odds
        events = driver.find_elements(By.CSS_SELECTOR, ".event-row")
        
        sport_odds = []
        for event in events:
            try:
                event_name = event.find_element(By.CSS_SELECTOR, ".event-name").text
                
                markets = event.find_elements(By.CSS_SELECTOR, ".market-group")
                for market in markets:
                    market_name = market.find_element(By.CSS_SELECTOR, ".market-name").text
                    selections = market.find_elements(By.CSS_SELECTOR, ".selection")
                    
                    market_odds = []
                    for selection in selections:
                        selection_name = selection.find_element(By.CSS_SELECTOR, ".selection-name").text
                        odds_value = selection.find_element(By.CSS_SELECTOR, ".odds").text
                        
                        market_odds.append({
                            "selection": selection_name,
                            "odds": parse_odds(odds_value)
                        })
                    
                    sport_odds.append({
                        "event": event_name,
                        "market": market_name,
                        "bookmaker": "Stake",
                        "odds": market_odds
                    })
            except Exception as e:
                logger.warning(f"Error processing an event in {sport}: {str(e)}")
                continue
        
        return sport_odds
        
    except TimeoutException:
        logger.warning(f"Timeout while loading {sport} on Stake")
        return []
    except Exception as e:
        logger.error(f"Error scraping {sport} from Stake: {str(e)}")
        return []

def parse_odds(odds_string):
    """Parse odds from string to float"""
    try:
        # Remove any whitespace and convert to float
        return float(odds_string.strip())
    except ValueError:
        logger.warning(f"Could not parse odds value: {odds_string}")
        return 0.0

# For testing purposes
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    odds = scrape_odds()
    print(f"Found odds for {len(odds)} sports")
    for sport, sport_odds in odds.items():
        print(f"{sport}: {len(sport_odds)} markets")
