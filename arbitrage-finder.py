import logging
from itertools import combinations

logger = logging.getLogger("arbitrage-bot.arbitrage")

def find_arbitrage_opportunities(bet365_odds, betmgm_odds, stake_odds):
    """Find arbitrage opportunities across the three bookmakers"""
    logger.info("Searching for arbitrage opportunities")
    
    opportunities = []
    
    # Combine all odds into a single structure for easier processing
    all_odds = {}
    
    # Process Bet365 odds
    for sport, markets in bet365_odds.items():
        if sport not in all_odds:
            all_odds[sport] = {}
            
        for market in markets:
            event = market["event"]
            market_type = market["market"]
            
            if event not in all_odds[sport]:
                all_odds[sport][event] = {}
                
            if market_type not in all_odds[sport][event]:
                all_odds[sport][event][market_type] = []
                
            all_odds[sport][event][market_type].append(market)
    
    # Process BetMGM odds
    for sport, markets in betmgm_odds.items():
        if sport not in all_odds:
            all_odds[sport] = {}
            
        for market in markets:
            event = market["event"]
            market_type = market["market"]
            
            if event not in all_odds[sport]:
                all_odds[sport][event] = {}
                
            if market_type not in all_odds[sport][event]:
                all_odds[sport][event][market_type] = []
                
            all_odds[sport][event][market_type].append(market)
    
    # Process Stake odds
    for sport, markets in stake_odds.items():
        if sport not in all_odds:
            all_odds[sport] = {}
            
        for market in markets:
            event = market["event"]
            market_type = market["market"]
            
            if event not in all_odds[sport]:
                all_odds[sport][event] = {}
                
            if market_type not in all_odds[sport][event]:
                all_odds[sport][event][market_type] = []
                
            all_odds[sport][event][market_type].append(market)
    
    # Check for arbitrage opportunities
    for sport in all_odds:
        for event in all_odds[sport]:
            for market_type in all_odds[sport][event]:
                # Only check if we have markets from at least 2 different bookmakers
                markets = all_odds[sport][event][market_type]
                bookmakers = set(market["bookmaker"] for market in markets)
                
                if len(bookmakers) >= 2:
                    # Check for arbitrage in this market
                    opportunity = check_arbitrage(sport, event, market_type, markets)
                    if opportunity:
                        opportunities.append(opportunity)
    
    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
    return opportunities

def check_arbitrage(sport, event, market_type, markets):
    """Check if there's an arbitrage opportunity in the given markets"""
    # For binary markets (2 outcomes, like Home/Away)
    if is_binary_market(market_type):
        return check_binary_arbitrage(sport, event, market_type, markets)
    
    # For 3-way markets (like Home/Draw/Away)
    elif is_three_way_market(market_type):
        return check_three_way_arbitrage(sport, event, market_type, markets)
    
    return None

def is_binary_market(market_type):
    """Check if the market is binary (2 outcomes)"""
    binary_markets = [
        "Money Line", "Head to Head", "Match Winner", 
        "To Win", "Match Result", "Spread", "Handicap"
    ]
    return any(market in market_type for market in binary_markets)

def is_three_way_market(market_type):
    """Check if the market is three-way (3 outcomes)"""
    three_way_markets = [
        "1X2", "Home/Draw/Away", "Match Result", "Full Time Result"
    ]
    return any(market in market_type for market in three_way_markets)

def check_binary_arbitrage(sport, event, market_type, markets):
    """Check for arbitrage in binary markets"""
    best_odds = {"selection1": 0, "selection2": 0, "bookmaker1": "", "bookmaker2": ""}
    
    # Find the best odds for each selection
    for market in markets:
        bookmaker = market["bookmaker"]
        
        if len(market["odds"]) != 2:
            continue
            
        odds_1 = market["odds"][0]["odds"]
        odds_2 = market["odds"][1]["odds"]
        
        selection_1 = market["odds"][0]["selection"]
        selection_2 = market["odds"][1]["selection"]
        
        if odds_1 > best_odds["selection1"]:
            best_odds["selection1"] = odds_1
            best_odds["bookmaker1"] = bookmaker
            best_odds["selection1_name"] = selection_1
        
        if odds_2 > best_odds["selection2"]:
            best_odds["selection2"] = odds_2
            best_odds["bookmaker2"] = bookmaker
            best_odds["selection2_name"] = selection_2
    
    # Check if we have an arbitrage opportunity
    if best_odds["selection1"] > 0 and best_odds["selection2"] > 0:
        margin = (1 / best_odds["selection1"]) + (1 / best_odds["selection2"])
        
        if margin < 1:
            # We have an arbitrage opportunity
            profit_percentage = ((1 / margin) - 1) * 100
            
            # Calculate optimal stakes for a $1000 total stake
            total_stake = 1000
            stake1 = total_stake * (1 / best_odds["selection1"]) / margin
            stake2 = total_stake * (1 / best_odds["selection2"]) / margin
            
            expected_return = stake1 * best_odds["selection1"]
            expected_profit = expected_return - total_stake
            
            return {
                "sport": sport,
                "event": event,
                "market": market_type,
                "profit_percentage": profit_percentage,
                "total_stake": total_stake,
                "expected_return": expected_return,
                "expected_profit": expected_profit,
                "bet1": {
                    "bookmaker": best_odds["bookmaker1"],
                    "selection": best_odds["selection1_name"],
                    "odds": best_odds["selection1"],
                    "stake": stake1,
                    "stake_percentage": (stake1 / total_stake) * 100
                },
                "bet2": {
                    "bookmaker": best_odds["bookmaker2"],
                    "selection": best_odds["selection2_name"],
                    "odds": best_odds["selection2"],
                    "stake": stake2,
                    "stake_percentage": (stake2 / total_stake) * 100
                }
            }
    
    return None

def check_three_way_arbitrage(sport, event, market_type, markets):
    """Check for arbitrage in three-way markets"""
    best_odds = {"selection1": 0, "selection2": 0, "selection3": 0, 
                "bookmaker1": "", "bookmaker2": "", "bookmaker3": ""}
    
    # Find the best odds for each selection
    for market in markets:
        bookmaker = market["bookmaker"]
        
        if len(market["odds"]) != 3:
            continue
            
        odds_1 = market["odds"][0]["odds"]
        odds_2 = market["odds"][1]["odds"]
        odds_3 = market["odds"][2]["odds"]
        
        selection_1 = market["odds"][0]["selection"]
        selection_2 = market["odds"][1]["selection"]
        selection_3 = market["odds"][2]["selection"]
        
        if odds_1 > best_odds["selection1"]:
            best_odds["selection1"] = odds_1
            best_odds["bookmaker1"] = bookmaker
            best_odds["selection1_name"] = selection_1
        
        if odds_2 > best_odds["selection2"]:
            best_odds["selection2"] = odds_2
            best_odds["bookmaker2"] = bookmaker
            best_odds["selection2_name"] = selection_2
            
        if odds_3 > best_odds["selection3"]:
            best_odds["selection3"] = odds_3
            best_odds["bookmaker3"] = bookmaker
            best_odds["selection3_name"] = selection_3
    
    # Check if we have an arbitrage opportunity
    if best_odds["selection1"] > 0 and best_odds["selection2"] > 0 and best_odds["selection3"] > 0:
        margin = (1 / best_odds["selection1"]) + (1 / best_odds["selection2"]) + (1 / best_odds["selection3"])
        
        if margin < 1:
            # We have an arbitrage opportunity
            profit_percentage = ((1 / margin) - 1) * 100
            
            # Calculate optimal stakes for a $1000 total stake
            total_stake = 1000
            stake1 = total_stake * (1 / best_odds["selection1"]) / margin
            stake2 = total_stake * (1 / best_odds["selection2"]) / margin
            stake3 = total_stake * (1 / best_odds["selection3"]) / margin
            
            expected_return = stake1 * best_odds["selection1"]
            expected_profit = expected_return - total_stake
            
            return {
                "sport": sport,
                "event": event,
                "market": market_type,
                "profit_percentage": profit_percentage,
                "total_stake": total_stake,
                "expected_return": expected_return,
                "expected_profit": expected_profit,
                "bet1": {
                    "bookmaker": best_odds["bookmaker1"],
                    "selection": best_odds["selection1_name"],
                    "odds": best_odds["selection1"],
                    "stake": stake1,
                    "stake_percentage": (stake1 / total_stake) * 100
                },
                "bet2": {
                    "bookmaker": best_odds["bookmaker2"],
                    "selection": best_odds["selection2_name"],
                    "odds": best_odds["selection2"],
                    "stake": stake2,
                    "stake_percentage": (stake2 / total_stake) * 100
                },
                "bet3": {
                    "bookmaker": best_odds["bookmaker3"],
                    "selection": best_odds["selection3_name"],
                    "odds": best_odds["selection3"],
                    "stake": stake3,
                    "stake_percentage": (stake3 / total_stake) * 100
                }
            }
    
    return None
