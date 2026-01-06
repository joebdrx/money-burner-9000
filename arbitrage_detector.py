"""Arbitrage opportunity detection and validation."""
import logging
from dataclasses import dataclass
from typing import Optional
from market_scanner import MarketPrice

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Validated arbitrage opportunity."""
    market_price: MarketPrice
    expected_profit: float
    expected_profit_pct: float
    position_size: float
    yes_cost: float
    no_cost: float
    total_cost: float
    
    def __str__(self) -> str:
        return (
            f"Arbitrage: {self.market_price.question[:40]}... | "
            f"Profit: ${self.expected_profit:.4f} ({self.expected_profit_pct:.2f}%) | "
            f"Cost: ${self.total_cost:.2f}"
        )


class ArbitrageDetector:
    """Detects and validates arbitrage opportunities."""
    
    def __init__(self, threshold: float = 0.99, min_profit: float = 0.02, 
                 max_position_size: float = 100.0):
        """Initialize the arbitrage detector.
        
        Args:
            threshold: Maximum acceptable total price (YES + NO)
            min_profit: Minimum profit in dollars to execute
            max_position_size: Maximum position size in dollars
        """
        self.threshold = threshold
        self.min_profit = min_profit
        self.max_position_size = max_position_size
    
    def validate_opportunity(self, market_price: MarketPrice) -> Optional[ArbitrageOpportunity]:
        """Validate if a market price represents a profitable arbitrage.
        
        Args:
            market_price: Market price data
            
        Returns:
            ArbitrageOpportunity if valid, None otherwise
        """
        # Check if total price is below threshold
        if market_price.total_price >= self.threshold:
            return None
        
        # Calculate expected profit per $1 position
        spread = market_price.arbitrage_spread
        
        # Determine optimal position size (limited by max_position_size)
        # We want to buy 1 YES and 1 NO, which costs (yes_price + no_price)
        position_size = min(self.max_position_size, self.max_position_size)
        
        # Calculate costs for buying both sides
        yes_cost = market_price.yes_price * position_size
        no_cost = market_price.no_price * position_size
        total_cost = yes_cost + no_cost
        
        # Expected payout is $1.00 per share
        expected_payout = position_size * 1.0
        
        # Expected profit
        expected_profit = expected_payout - total_cost
        expected_profit_pct = (expected_profit / total_cost) * 100
        
        # Check if profit meets minimum threshold
        if expected_profit < self.min_profit:
            logger.debug(
                f"Profit ${expected_profit:.4f} below minimum ${self.min_profit}"
            )
            return None
        
        opportunity = ArbitrageOpportunity(
            market_price=market_price,
            expected_profit=expected_profit,
            expected_profit_pct=expected_profit_pct,
            position_size=position_size,
            yes_cost=yes_cost,
            no_cost=no_cost,
            total_cost=total_cost
        )
        
        logger.info(f"Valid opportunity: {opportunity}")
        return opportunity
    
    def filter_opportunities(self, market_prices: list[MarketPrice]) -> list[ArbitrageOpportunity]:
        """Filter and validate a list of market prices for arbitrage.
        
        Args:
            market_prices: List of market price data
            
        Returns:
            List of validated arbitrage opportunities
        """
        opportunities = []
        
        for price in market_prices:
            opportunity = self.validate_opportunity(price)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by expected profit (highest first)
        opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
        
        logger.info(f"Found {len(opportunities)} valid arbitrage opportunities")
        return opportunities
