#!/usr/bin/env python3
"""Entry point for Polymarket arbitrage bot."""
import sys
import logging
import coloredlogs

from config import BotConfig
from bot import PolymarketArbitrageBot


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure coloredlogs
    coloredlogs.install(
        level=log_level,
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('web3').setLevel(logging.WARNING)


def main():
    """Main entry point."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         Polymarket Arbitrage Bot                         ║
    ║         Binary Market Price Gap Exploiter                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = BotConfig.from_env()
        config.validate()
        
        # Setup logging
        setup_logging(config.log_level)
        logger = logging.getLogger(__name__)
        
        # Display configuration
        logger.info("=" * 60)
        logger.info("BOT CONFIGURATION")
        logger.info("=" * 60)
        logger.info(f"Arbitrage Threshold: {config.arbitrage_threshold}")
        logger.info(f"Minimum Profit: ${config.min_profit}")
        logger.info(f"Scan Interval: {config.scan_interval}s")
        logger.info(f"Max Position Size: ${config.max_position_size}")
        logger.info(f"Dry Run Mode: {config.dry_run}")
        logger.info("=" * 60)
        
        if config.dry_run:
            logger.warning("⚠️  DRY RUN MODE ENABLED - No real trades will be executed")
        else:
            logger.warning("🔴 LIVE TRADING MODE - Real money will be used!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Exiting...")
                return
        
        # Initialize and run bot
        bot = PolymarketArbitrageBot(config)
        bot.run()
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. You have created a .env file (copy from .env.example)")
        print("2. PRIVATE_KEY is set in .env")
        print("3. All configuration values are valid")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
