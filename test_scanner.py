#!/usr/bin/env python3
"""Test script to verify market scanner functionality."""
import logging
import sys
from config import BotConfig
from bot import PolymarketArbitrageBot

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)


def test_scanner():
    """Test the market scanner by doing a single scan."""
    print("\n" + "="*60)
    print("Testing Polymarket Arbitrage Bot - Scanner Test")
    print("="*60 + "\n")
    
    try:
        # Load config
        config = BotConfig.from_env()
        config.validate()
        
        print(f"Configuration loaded:")
        print(f"  - Arbitrage Threshold: {config.arbitrage_threshold}")
        print(f"  - Min Profit: ${config.min_profit}")
        print(f"  - Max Position: ${config.max_position_size}")
        print(f"  - Dry Run: {config.dry_run}\n")
        
        # Create bot
        print("Initializing bot...")
        bot = PolymarketArbitrageBot(config)
        
        # Perform single scan
        print("\nScanning markets for arbitrage opportunities...\n")
        opportunities = bot.scan_once()
        
        # Display results
        print("\n" + "="*60)
        print(f"SCAN RESULTS: Found {len(opportunities)} opportunities")
        print("="*60)
        
        if opportunities:
            print("\nTop Opportunities:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"\n{i}. {opp.market_price.question[:60]}...")
                print(f"   YES: ${opp.market_price.yes_price:.4f}")
                print(f"   NO:  ${opp.market_price.no_price:.4f}")
                print(f"   Total: ${opp.market_price.total_price:.4f}")
                print(f"   Expected Profit: ${opp.expected_profit:.4f} ({opp.expected_profit_pct:.2f}%)")
        else:
            print("\nNo arbitrage opportunities found at current thresholds.")
            print("Try adjusting ARBITRAGE_THRESHOLD in .env")
        
        print("\n" + "="*60)
        print("Test completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_scanner()
