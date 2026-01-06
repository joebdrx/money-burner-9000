"""Market scanner for monitoring Polymarket prices."""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BookParams

logger = logging.getLogger(__name__)


@dataclass
class MarketPrice:
    """Price data for a binary market."""
    token_id: str
    yes_price: float
    no_price: float
    yes_token_id: str
    no_token_id: str
    condition_id: str
    question: str
    total_price: float
    
    @property
    def arbitrage_spread(self) -> float:
        """Calculate the arbitrage spread (1.0 - total_price)."""
        return 1.0 - self.total_price


class MarketScanner:
    """Scans Polymarket for price data."""
    
    def __init__(self, client: ClobClient):
        """Initialize the market scanner.
        
        Args:
            client: Authenticated Polymarket CLOB client
        """
        self.client = client
        self._market_cache: Dict[str, dict] = {}
    
    def get_active_markets(self, limit: int = 100) -> List[dict]:
        """Fetch active binary markets.

        Args:
            limit: Maximum number of markets to return

        Returns:
            List of market data dictionaries
        """
        try:
            response = self.client.get_simplified_markets()

            # Extract markets from response
            if isinstance(response, dict):
                markets = response.get('data', [])
            else:
                markets = response

            # Filter for binary markets (YES/NO) with tradable prices
            binary_markets = []
            for market in markets:
                # Skip if not a dict
                if not isinstance(market, dict):
                    continue

                # Check if market has exactly 2 outcomes (YES/NO)
                tokens = market.get('tokens', [])
                if len(tokens) != 2:
                    continue

                # Check if prices are valid and tradable (not fully resolved)
                # Markets with prices at 0 or 1 are resolved
                p0 = tokens[0].get('price', 0)
                p1 = tokens[1].get('price', 0)

                # Skip fully resolved markets (prices are exactly 0 or 1)
                if (p0 == 0 or p0 == 1) and (p1 == 0 or p1 == 1):
                    continue

                # Skip markets with invalid prices
                if p0 <= 0 or p1 <= 0:
                    continue

                binary_markets.append(market)
                # Cache market metadata
                self._market_cache[market['condition_id']] = market

                if len(binary_markets) >= limit:
                    break

            logger.info(f"Found {len(binary_markets)} active binary markets")
            return binary_markets

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_market_prices(self, condition_id: str) -> Optional[MarketPrice]:
        """Get current prices for a binary market.

        Args:
            condition_id: The market condition ID

        Returns:
            MarketPrice object or None if error
        """
        try:
            # Get market metadata from cache
            market = self._market_cache.get(condition_id)
            if not market:
                logger.warning(f"Market {condition_id} not in cache")
                return None

            tokens = market.get('tokens', [])
            if len(tokens) != 2:
                return None

            # Get token data for both outcomes
            token_0 = tokens[0]
            token_1 = tokens[1]

            # Get prices directly from cached market data
            price_0 = float(token_0.get('price', 0))
            price_1 = float(token_1.get('price', 0))

            # Skip if prices are invalid
            if price_0 <= 0 or price_1 <= 0:
                logger.debug(f"Invalid prices for {condition_id}: {price_0}, {price_1}")
                return None

            # Create descriptive question from outcomes
            outcome_0 = token_0.get('outcome', 'Option 1')
            outcome_1 = token_1.get('outcome', 'Option 2')
            question = f"{outcome_0} vs {outcome_1}"

            return MarketPrice(
                token_id=condition_id,
                yes_price=price_0,
                no_price=price_1,
                yes_token_id=str(token_0['token_id']),
                no_token_id=str(token_1['token_id']),
                condition_id=condition_id,
                question=question,
                total_price=price_0 + price_1
            )

        except Exception as e:
            logger.error(f"Error getting prices for {condition_id}: {e}")
            return None
    
    def _get_token_price(self, token_id: str, side: str = 'BUY') -> Optional[float]:
        """Get current price for a specific token.
        
        Args:
            token_id: The token ID
            side: BUY or SELL
            
        Returns:
            Price as float or None
        """
        try:
            price = self.client.get_price(token_id, side=side)
            return float(price['price']) if price else None
        except Exception as e:
            logger.debug(f"Error getting price for token {token_id}: {e}")
            return None
    
    def scan_for_arbitrage(self, threshold: float = 0.99) -> List[MarketPrice]:
        """Scan all markets for arbitrage opportunities.
        
        Args:
            threshold: Maximum acceptable total price (YES + NO)
            
        Returns:
            List of markets with arbitrage opportunities
        """
        opportunities = []
        
        # Get active markets
        markets = self.get_active_markets()
        
        for market in markets:
            condition_id = market['condition_id']
            prices = self.get_market_prices(condition_id)
            
            if prices and prices.total_price < threshold:
                logger.info(
                    f"Arbitrage opportunity: {prices.question[:50]}... "
                    f"YES={prices.yes_price:.4f} NO={prices.no_price:.4f} "
                    f"Total={prices.total_price:.4f} Spread={prices.arbitrage_spread:.4f}"
                )
                opportunities.append(prices)
        
        return opportunities
