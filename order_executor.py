"""Order execution for arbitrage trades."""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY
from arbitrage_detector import ArbitrageOpportunity

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of an order execution."""
    success: bool
    yes_order_id: Optional[str] = None
    no_order_id: Optional[str] = None
    yes_filled: bool = False
    no_filled: bool = False
    error: Optional[str] = None
    
    @property
    def both_filled(self) -> bool:
        """Check if both YES and NO orders were filled."""
        return self.yes_filled and self.no_filled


class OrderExecutor:
    """Executes arbitrage trades on Polymarket."""
    
    def __init__(self, client: ClobClient, dry_run: bool = True):
        """Initialize the order executor.
        
        Args:
            client: Authenticated Polymarket CLOB client
            dry_run: If True, simulate trades without executing
        """
        self.client = client
        self.dry_run = dry_run
    
    def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> ExecutionResult:
        """Execute an arbitrage trade by buying both YES and NO.
        
        Args:
            opportunity: Validated arbitrage opportunity
            
        Returns:
            ExecutionResult with trade details
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {opportunity}")
            return ExecutionResult(
                success=True,
                yes_order_id="dry_run_yes",
                no_order_id="dry_run_no",
                yes_filled=True,
                no_filled=True
            )
        
        try:
            # Execute both orders simultaneously
            yes_result = self._place_market_order(
                token_id=opportunity.market_price.yes_token_id,
                amount=opportunity.position_size,
                side="YES"
            )
            
            no_result = self._place_market_order(
                token_id=opportunity.market_price.no_token_id,
                amount=opportunity.position_size,
                side="NO"
            )
            
            # Check if both orders succeeded
            success = yes_result[0] and no_result[0]
            
            if not success:
                error_msg = []
                if not yes_result[0]:
                    error_msg.append(f"YES order failed: {yes_result[2]}")
                if not no_result[0]:
                    error_msg.append(f"NO order failed: {no_result[2]}")
                
                logger.error(f"Execution failed: {' | '.join(error_msg)}")
                
                # TODO: Implement rollback logic if only one side filled
                
                return ExecutionResult(
                    success=False,
                    yes_order_id=yes_result[1],
                    no_order_id=no_result[1],
                    yes_filled=yes_result[0],
                    no_filled=no_result[0],
                    error=' | '.join(error_msg)
                )
            
            logger.info(
                f"Arbitrage executed successfully! "
                f"YES order: {yes_result[1]}, NO order: {no_result[1]}"
            )
            
            return ExecutionResult(
                success=True,
                yes_order_id=yes_result[1],
                no_order_id=no_result[1],
                yes_filled=True,
                no_filled=True
            )
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return ExecutionResult(success=False, error=str(e))
    
    def _place_market_order(self, token_id: str, amount: float, 
                           side: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Place a market order for a token.
        
        Args:
            token_id: The token ID to trade
            amount: Amount in shares
            side: "YES" or "NO" (for logging)
            
        Returns:
            Tuple of (success, order_id, error_message)
        """
        try:
            # Create market order
            order = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=BUY,  # Always buying both sides
                order_type=OrderType.FOK  # Fill-or-kill for atomicity
            )
            
            # Sign the order
            signed_order = self.client.create_market_order(order)
            
            # Post the order
            response = self.client.post_order(signed_order, OrderType.FOK)
            
            order_id = response.get('orderID')
            
            logger.info(f"{side} order placed: {order_id}")
            return (True, order_id, None)
            
        except Exception as e:
            logger.error(f"Error placing {side} order: {e}")
            return (False, None, str(e))
