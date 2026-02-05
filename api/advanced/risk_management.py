"""
Risk Management Engine
Position sizing, stop-loss, take-profit, and exposure controls
"""
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PositionSizeMethod(Enum):
    """Position sizing methods"""
    FIXED = "fixed"
    KELLY = "kelly"
    VOLATILITY = "volatility"
    RISK_PARITY = "risk_parity"
    MAX_LOSS = "max_loss"


@dataclass
class Position:
    """Trading position"""
    symbol: str
    size: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def pnl(self) -> float:
        """Current profit/loss"""
        return (self.current_price - self.entry_price) * self.size
    
    @property
    def pnl_pct(self) -> float:
        """Current profit/loss percentage"""
        return (self.current_price - self.entry_price) / self.entry_price


@dataclass
class RiskLimits:
    """Risk management limits"""
    max_position_size: float = 0.25  # Max 25% per position
    max_portfolio_leverage: float = 1.0  # No leverage by default
    max_daily_loss: float = 0.02  # Max 2% daily loss
    max_drawdown: float = 0.15  # Max 15% drawdown
    max_correlation: float = 0.7  # Max correlation between positions
    min_sharpe_ratio: float = 0.5  # Min Sharpe ratio to maintain position


class RiskManager:
    """
    Comprehensive risk management engine
    Handles position sizing, stop-loss, take-profit, and exposure controls
    """
    
    def __init__(
        self,
        initial_capital: float,
        risk_limits: Optional[RiskLimits] = None
    ):
        """
        Initialize risk manager
        
        Args:
            initial_capital: Starting capital
            risk_limits: Risk limit configuration
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_limits = risk_limits or RiskLimits()
        self.positions: Dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.peak_capital = initial_capital
    
    def calculate_position_size(
        self,
        symbol: str,
        signal_strength: float,
        current_price: float,
        volatility: float,
        method: PositionSizeMethod = PositionSizeMethod.VOLATILITY
    ) -> float:
        """
        Calculate optimal position size
        
        Args:
            symbol: Trading symbol
            signal_strength: Signal strength (0-1)
            current_price: Current asset price
            volatility: Asset volatility
            method: Position sizing method
        
        Returns:
            Position size (number of shares/contracts)
        """
        if method == PositionSizeMethod.FIXED:
            return self._fixed_size(current_price)
        
        elif method == PositionSizeMethod.KELLY:
            return self._kelly_size(signal_strength, current_price, volatility)
        
        elif method == PositionSizeMethod.VOLATILITY:
            return self._volatility_size(current_price, volatility)
        
        elif method == PositionSizeMethod.MAX_LOSS:
            return self._max_loss_size(current_price, volatility)
        
        else:
            logger.warning(f"Unknown sizing method: {method}, using fixed")
            return self._fixed_size(current_price)
    
    def _fixed_size(self, current_price: float) -> float:
        """Fixed percentage position sizing"""
        position_value = self.current_capital * self.risk_limits.max_position_size
        return position_value / current_price
    
    def _kelly_size(
        self,
        win_prob: float,
        current_price: float,
        expected_return: float
    ) -> float:
        """Kelly criterion position sizing"""
        # Kelly formula: f = (p * b - q) / b
        # where p = win probability, q = 1-p, b = win/loss ratio
        
        if win_prob <= 0 or win_prob >= 1:
            return 0.0
        
        # Assume win/loss ratio from expected return
        win_loss_ratio = max(expected_return, 0.01)
        
        kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        
        # Use half Kelly for safety
        kelly_fraction = max(0, min(kelly_fraction * 0.5, self.risk_limits.max_position_size))
        
        position_value = self.current_capital * kelly_fraction
        return position_value / current_price
    
    def _volatility_size(self, current_price: float, volatility: float) -> float:
        """Volatility-adjusted position sizing (inverse volatility)"""
        if volatility <= 0:
            return 0.0
        
        # Target volatility approach
        target_vol = 0.15  # 15% annual volatility target
        vol_scalar = target_vol / volatility
        
        # Scale position size
        base_size = self.current_capital * self.risk_limits.max_position_size
        adjusted_size = base_size * vol_scalar
        
        # Cap at max position size
        max_value = self.current_capital * self.risk_limits.max_position_size
        adjusted_size = min(adjusted_size, max_value)
        
        return adjusted_size / current_price
    
    def _max_loss_size(self, current_price: float, stop_loss_pct: float) -> float:
        """Position sizing based on maximum acceptable loss"""
        if stop_loss_pct <= 0:
            return 0.0
        
        # Calculate size based on max loss tolerance
        max_loss_amount = self.current_capital * self.risk_limits.max_daily_loss
        
        # Size = max_loss / (price * stop_loss_pct)
        size = max_loss_amount / (current_price * stop_loss_pct)
        
        # Cap at max position size
        max_shares = (self.current_capital * self.risk_limits.max_position_size) / current_price
        return min(size, max_shares)
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        volatility: float,
        atr: Optional[float] = None,
        method: str = "atr"
    ) -> float:
        """
        Calculate stop-loss level
        
        Args:
            entry_price: Entry price
            volatility: Asset volatility
            atr: Average True Range (if available)
            method: Stop-loss method (atr, volatility, fixed)
        
        Returns:
            Stop-loss price level
        """
        if method == "atr" and atr is not None:
            # ATR-based stop: entry - 2*ATR
            return entry_price - (2 * atr)
        
        elif method == "volatility":
            # Volatility-based: entry - 2*daily_volatility
            daily_vol = volatility / np.sqrt(252)
            return entry_price * (1 - 2 * daily_vol)
        
        else:
            # Fixed percentage stop
            return entry_price * 0.97  # 3% stop-loss
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate take-profit level
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            risk_reward_ratio: Reward/risk ratio (default 2:1)
        
        Returns:
            Take-profit price level
        """
        risk = entry_price - stop_loss
        reward = risk * risk_reward_ratio
        return entry_price + reward
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """
        Check if current positions violate risk limits
        
        Returns:
            Dictionary of risk limit checks
        """
        total_exposure = sum(abs(p.size * p.current_price) for p in self.positions.values())
        leverage = total_exposure / self.current_capital
        
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        
        daily_loss_pct = self.daily_pnl / self.current_capital if self.current_capital > 0 else 0
        
        return {
            "within_position_limit": all(
                abs(p.size * p.current_price) / self.current_capital <= self.risk_limits.max_position_size
                for p in self.positions.values()
            ),
            "within_leverage_limit": leverage <= self.risk_limits.max_portfolio_leverage,
            "within_daily_loss_limit": daily_loss_pct >= -self.risk_limits.max_daily_loss,
            "within_drawdown_limit": current_drawdown <= self.risk_limits.max_drawdown,
        }
    
    def should_close_position(self, symbol: str) -> Dict[str, bool]:
        """
        Check if position should be closed based on risk rules
        
        Args:
            symbol: Position symbol
        
        Returns:
            Dictionary of close signals
        """
        if symbol not in self.positions:
            return {"stop_loss": False, "take_profit": False, "risk_limit": False}
        
        position = self.positions[symbol]
        
        signals = {
            "stop_loss": False,
            "take_profit": False,
            "risk_limit": False
        }
        
        # Check stop-loss
        if position.stop_loss is not None:
            if position.current_price <= position.stop_loss:
                signals["stop_loss"] = True
        
        # Check take-profit
        if position.take_profit is not None:
            if position.current_price >= position.take_profit:
                signals["take_profit"] = True
        
        # Check risk limits
        risk_checks = self.check_risk_limits()
        if not all(risk_checks.values()):
            signals["risk_limit"] = True
        
        return signals
    
    def update_position(
        self,
        symbol: str,
        current_price: float,
        trailing_stop: bool = False,
        trailing_stop_pct: float = 0.02
    ):
        """
        Update position with current price and trailing stop
        
        Args:
            symbol: Position symbol
            current_price: Current market price
            trailing_stop: Whether to use trailing stop
            trailing_stop_pct: Trailing stop percentage
        """
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.current_price = current_price
        
        # Update trailing stop
        if trailing_stop and position.stop_loss is not None:
            # Calculate new stop based on highest price
            new_stop = current_price * (1 - trailing_stop_pct)
            if new_stop > position.stop_loss:
                position.stop_loss = new_stop
                logger.info(f"Updated trailing stop for {symbol} to {new_stop:.2f}")
    
    def add_position(
        self,
        symbol: str,
        size: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ):
        """Add new position"""
        position = Position(
            symbol=symbol,
            size=size,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        self.positions[symbol] = position
        logger.info(f"Added position: {symbol} size={size} entry={entry_price}")
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """Close position and return P&L"""
        if symbol not in self.positions:
            return {"error": "Position not found"}
        
        position = self.positions[symbol]
        position.current_price = exit_price
        
        pnl = position.pnl
        pnl_pct = position.pnl_pct
        
        # Update capital
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        # Update peak for drawdown calculation
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Closed position: {symbol} P&L={pnl:.2f} ({pnl_pct:.2%})")
        
        return {
            "symbol": symbol,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "exit_price": exit_price,
            "current_capital": self.current_capital
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        total_value = self.current_capital
        total_pnl = sum(p.pnl for p in self.positions.values())
        
        return {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "total_return": (self.current_capital - self.initial_capital) / self.initial_capital,
            "n_positions": len(self.positions),
            "total_exposure": sum(abs(p.size * p.current_price) for p in self.positions.values()),
            "unrealized_pnl": total_pnl,
            "daily_pnl": self.daily_pnl,
            "peak_capital": self.peak_capital,
            "current_drawdown": (self.peak_capital - self.current_capital) / self.peak_capital,
            "positions": [
                {
                    "symbol": p.symbol,
                    "size": p.size,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "pnl": p.pnl,
                    "pnl_pct": p.pnl_pct,
                    "stop_loss": p.stop_loss,
                    "take_profit": p.take_profit
                }
                for p in self.positions.values()
            ]
        }
