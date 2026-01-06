"""Configuration management for Polymarket arbitrage bot."""
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Bot configuration settings."""
    
    # Authentication
    private_key: str
    chain_id: int = 137  # Polygon mainnet
    
    # Trading parameters
    arbitrage_threshold: float = 0.99  # Combined YES+NO price threshold
    min_profit: float = 0.02  # Minimum profit to execute trade
    scan_interval: int = 2  # Seconds between scans
    max_position_size: float = 100.0  # Maximum $ per position
    
    # Operation mode
    dry_run: bool = True  # Set to False for live trading
    log_level: str = "INFO"
    
    # Target markets
    target_markets: List[str] = None  # List of token IDs to monitor
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Load configuration from environment variables."""
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable is required")
        
        # Parse target markets
        target_markets_str = os.getenv('TARGET_MARKETS', '')
        target_markets = [m.strip() for m in target_markets_str.split(',') if m.strip()]
        
        return cls(
            private_key=private_key,
            chain_id=int(os.getenv('CHAIN_ID', '137')),
            arbitrage_threshold=float(os.getenv('ARBITRAGE_THRESHOLD', '0.99')),
            min_profit=float(os.getenv('MIN_PROFIT', '0.02')),
            scan_interval=int(os.getenv('SCAN_INTERVAL', '2')),
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', '100')),
            dry_run=os.getenv('DRY_RUN', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            target_markets=target_markets if target_markets else None
        )
    
    def validate(self):
        """Validate configuration settings."""
        if self.arbitrage_threshold >= 1.0:
            raise ValueError("arbitrage_threshold must be < 1.0")
        if self.min_profit <= 0:
            raise ValueError("min_profit must be > 0")
        if self.scan_interval <= 0:
            raise ValueError("scan_interval must be > 0")
        if self.max_position_size <= 0:
            raise ValueError("max_position_size must be > 0")
