"""Main arbitrage bot orchestration."""
import logging
import time
from typing import List
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

from config import BotConfig
from market_scanner import MarketScanner, MarketPrice
from arbitrage_detector import ArbitrageDetector, ArbitrageOpportunity
from order_executor import OrderExecutor, ExecutionResult
from position_manager import PositionManager, Position

logger = logging.getLogger(__name__)


class PolymarketArbitrageBot:
    """Main arbitrage bot for Polymarket."""
    
    def __init__(self, config: BotConfig):
        """Initialize the arbitrage bot.
        
        Args:
            config: Bot configuration
        """
        self.config = config
        
        # Initialize Polymarket client
        logger.info("Initializing Polymarket client...")
        self.client = self._create_client()
        
        # Initialize components
        self.scanner = MarketScanner(self.client)
        self.detector = ArbitrageDetector(
            threshold=config.arbitrage_threshold,
            min_profit=config.min_profit,
            max_position_size=config.max_position_size
        )
        self.executor = OrderExecutor(self.client, dry_run=config.dry_run)
        self.position_manager = PositionManager()
        
        self.running = False
        
        logger.info(f"Bot initialized (DRY RUN: {config.dry_run})")
    
    def _create_client(self) -> ClobClient:
        """Create and authenticate Polymarket CLOB client.
        
        Returns:
            Authenticated ClobClient
        """
        try:
            # Create client with private key
            # For now, we'll use public endpoints (Level 0)
            # Full trading requires L2 authentication with API credentials
            
            host = "https://clob.polymarket.com"
            chain_id = self.config.chain_id
            
            # Initialize client
            client = ClobClient(
                host=host,
                chain_id=chain_id,
                key=self.config.private_key  # Private key for authentication
            )
            
            logger.info("Polymarket client created successfully")
            return client
            
        except Exception as e:
            logger.error(f"Error creating Polymarket client: {e}")
            raise
    
    def scan_once(self) -> List[ArbitrageOpportunity]:
        """Perform a single scan for arbitrage opportunities.
        
        Returns:
            List of valid arbitrage opportunities
        """
        logger.info("Scanning markets for arbitrage opportunities...")
        
        # Scan markets for price gaps
        market_prices = self.scanner.scan_for_arbitrage(
            threshold=self.config.arbitrage_threshold
        )
        
        # Validate and filter opportunities
        opportunities = self.detector.filter_opportunities(market_prices)
        
        logger.info(f"Found {len(opportunities)} valid opportunities")
        return opportunities
    
    def execute_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute a single arbitrage opportunity.
        
        Args:
            opportunity: The opportunity to execute
            
        Returns:
            True if execution successful
        """
        logger.info(f"Executing: {opportunity}")
        
        # Execute the trade
        result = self.executor.execute_arbitrage(opportunity)
        
        if result.success and result.both_filled:
            # Create position
            position = Position(
                condition_id=opportunity.market_price.condition_id,
                question=opportunity.market_price.question,
                yes_token_id=opportunity.market_price.yes_token_id,
                no_token_id=opportunity.market_price.no_token_id,
                position_size=opportunity.position_size,
                yes_cost=opportunity.yes_cost,
                no_cost=opportunity.no_cost,
                total_cost=opportunity.total_cost,
                expected_profit=opportunity.expected_profit,
                yes_order_id=result.yes_order_id,
                no_order_id=result.no_order_id
            )
            
            # Track position
            self.position_manager.add_position(position)
            
            logger.info(f"Position created successfully")
            return True
        else:
            logger.warning(f"Execution failed: {result.error}")
            return False
    
    def run(self) -> None:
        """Run the bot in continuous mode."""
        self.running = True
        logger.info("Starting arbitrage bot...")
        
        scan_count = 0
        
        try:
            while self.running:
                scan_count += 1
                logger.info(f"Scan #{scan_count}")
                
                # Find opportunities
                opportunities = self.scan_once()
                
                # Execute opportunities
                for opportunity in opportunities:
                    try:
                        self.execute_opportunity(opportunity)
                        # Small delay between executions
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error executing opportunity: {e}")
                
                # Print stats periodically
                if scan_count % 10 == 0:
                    self.position_manager.print_stats()
                
                # Wait before next scan
                logger.info(f"Waiting {self.config.scan_interval}s until next scan...")
                time.sleep(self.config.scan_interval)
                
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
            self.stop()
    
    def stop(self) -> None:
        """Stop the bot."""
        self.running = False
        self.position_manager.print_stats()
        logger.info("Bot stopped")
