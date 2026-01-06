"""Position and PnL tracking for arbitrage trades."""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an arbitrage position (both YES and NO sides)."""
    condition_id: str
    question: str
    yes_token_id: str
    no_token_id: str
    position_size: float
    yes_cost: float
    no_cost: float
    total_cost: float
    expected_profit: float
    timestamp: datetime = field(default_factory=datetime.now)
    yes_order_id: Optional[str] = None
    no_order_id: Optional[str] = None
    resolved: bool = False
    actual_payout: Optional[float] = None
    actual_profit: Optional[float] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if both sides of the position are filled."""
        return bool(self.yes_order_id and self.no_order_id)
    
    def to_dict(self) -> dict:
        """Convert position to dictionary."""
        return {
            'condition_id': self.condition_id,
            'question': self.question,
            'yes_token_id': self.yes_token_id,
            'no_token_id': self.no_token_id,
            'position_size': self.position_size,
            'yes_cost': self.yes_cost,
            'no_cost': self.no_cost,
            'total_cost': self.total_cost,
            'expected_profit': self.expected_profit,
            'timestamp': self.timestamp.isoformat(),
            'yes_order_id': self.yes_order_id,
            'no_order_id': self.no_order_id,
            'resolved': self.resolved,
            'actual_payout': self.actual_payout,
            'actual_profit': self.actual_profit
        }


class PositionManager:
    """Manages arbitrage positions and tracks PnL."""
    
    def __init__(self, storage_file: str = 'positions.json'):
        """Initialize the position manager.
        
        Args:
            storage_file: File path to store positions
        """
        self.storage_file = storage_file
        self.active_positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self._load_positions()
    
    def add_position(self, position: Position) -> None:
        """Add a new position.
        
        Args:
            position: Position to add
        """
        self.active_positions[position.condition_id] = position
        logger.info(f"Added position: {position.question[:50]}...")
        self._save_positions()
    
    def update_position(self, condition_id: str, **kwargs) -> None:
        """Update an existing position.
        
        Args:
            condition_id: The position condition ID
            **kwargs: Fields to update
        """
        if condition_id in self.active_positions:
            position = self.active_positions[condition_id]
            for key, value in kwargs.items():
                if hasattr(position, key):
                    setattr(position, key, value)
            self._save_positions()
            logger.debug(f"Updated position {condition_id}")
    
    def close_position(self, condition_id: str, actual_payout: float) -> None:
        """Close a position and calculate actual profit.
        
        Args:
            condition_id: The position condition ID
            actual_payout: Actual payout received
        """
        if condition_id in self.active_positions:
            position = self.active_positions.pop(condition_id)
            position.resolved = True
            position.actual_payout = actual_payout
            position.actual_profit = actual_payout - position.total_cost
            
            self.closed_positions.append(position)
            self._save_positions()
            
            logger.info(
                f"Closed position: {position.question[:50]}... | "
                f"Profit: ${position.actual_profit:.4f}"
            )
    
    def get_stats(self) -> dict:
        """Get portfolio statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        total_positions = len(self.active_positions) + len(self.closed_positions)
        
        if not self.closed_positions:
            return {
                'total_positions': total_positions,
                'active_positions': len(self.active_positions),
                'closed_positions': 0,
                'total_profit': 0.0,
                'win_rate': 0.0,
                'avg_profit_per_trade': 0.0,
                'total_invested': sum(p.total_cost for p in self.active_positions.values())
            }
        
        total_profit = sum(p.actual_profit for p in self.closed_positions if p.actual_profit)
        wins = sum(1 for p in self.closed_positions if p.actual_profit and p.actual_profit > 0)
        win_rate = (wins / len(self.closed_positions)) * 100 if self.closed_positions else 0
        avg_profit = total_profit / len(self.closed_positions) if self.closed_positions else 0
        
        return {
            'total_positions': total_positions,
            'active_positions': len(self.active_positions),
            'closed_positions': len(self.closed_positions),
            'total_profit': total_profit,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit,
            'total_invested': sum(p.total_cost for p in self.active_positions.values())
        }
    
    def print_stats(self) -> None:
        """Print portfolio statistics to logger."""
        stats = self.get_stats()
        
        logger.info("=" * 60)
        logger.info("PORTFOLIO STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total Positions: {stats['total_positions']}")
        logger.info(f"Active Positions: {stats['active_positions']}")
        logger.info(f"Closed Positions: {stats['closed_positions']}")
        logger.info(f"Total Profit: ${stats['total_profit']:.2f}")
        logger.info(f"Win Rate: {stats['win_rate']:.2f}%")
        logger.info(f"Avg Profit/Trade: ${stats['avg_profit_per_trade']:.4f}")
        logger.info(f"Total Invested: ${stats['total_invested']:.2f}")
        logger.info("=" * 60)
    
    def _save_positions(self) -> None:
        """Save positions to file."""
        try:
            data = {
                'active': [p.to_dict() for p in self.active_positions.values()],
                'closed': [p.to_dict() for p in self.closed_positions]
            }
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving positions: {e}")
    
    def _load_positions(self) -> None:
        """Load positions from file."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                # TODO: Deserialize positions from dict
                logger.info(f"Loaded {len(data.get('active', []))} active positions")
        except FileNotFoundError:
            logger.info("No existing positions file found")
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
