"""
Custom Technical Indicators Framework
Extensible system for technical indicators with TA-Lib integration
"""
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """Indicator categories"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    CUSTOM = "custom"


@dataclass
class IndicatorMetadata:
    """Metadata for an indicator"""
    name: str
    category: IndicatorCategory
    description: str
    parameters: Dict[str, Any]
    outputs: List[str]


class BaseIndicator:
    """Base class for all technical indicators"""
    
    def __init__(self, name: str, category: IndicatorCategory, description: str):
        self.name = name
        self.category = category
        self.description = description
        self.parameters = {}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Calculate indicator values
        
        Args:
            data: Dictionary with 'open', 'high', 'low', 'close', 'volume'
        
        Returns:
            Dictionary with indicator outputs
        """
        raise NotImplementedError("Subclasses must implement calculate()")
    
    def validate_data(self, data: Dict[str, np.ndarray]) -> bool:
        """Validate input data"""
        required_fields = ['close']
        return all(field in data for field in required_fields)


class MovingAverage(BaseIndicator):
    """Simple Moving Average indicator"""
    
    def __init__(self, period: int = 20):
        super().__init__(
            name="SMA",
            category=IndicatorCategory.TREND,
            description=f"Simple Moving Average ({period} period)"
        )
        self.period = period
        self.parameters = {"period": period}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate SMA"""
        if not self.validate_data(data):
            raise ValueError("Invalid data: 'close' required")
        
        close = data['close']
        sma = np.convolve(close, np.ones(self.period)/self.period, mode='valid')
        
        # Pad with NaN for initial period
        result = np.full(len(close), np.nan)
        result[self.period-1:] = sma
        
        return {"sma": result}


class ExponentialMovingAverage(BaseIndicator):
    """Exponential Moving Average indicator"""
    
    def __init__(self, period: int = 20):
        super().__init__(
            name="EMA",
            category=IndicatorCategory.TREND,
            description=f"Exponential Moving Average ({period} period)"
        )
        self.period = period
        self.parameters = {"period": period}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate EMA"""
        if not self.validate_data(data):
            raise ValueError("Invalid data: 'close' required")
        
        close = data['close']
        alpha = 2 / (self.period + 1)
        
        ema = np.zeros(len(close))
        ema[0] = close[0]
        
        for i in range(1, len(close)):
            ema[i] = alpha * close[i] + (1 - alpha) * ema[i-1]
        
        return {"ema": ema}


class RSI(BaseIndicator):
    """Relative Strength Index indicator"""
    
    def __init__(self, period: int = 14):
        super().__init__(
            name="RSI",
            category=IndicatorCategory.MOMENTUM,
            description=f"Relative Strength Index ({period} period)"
        )
        self.period = period
        self.parameters = {"period": period}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate RSI"""
        if not self.validate_data(data):
            raise ValueError("Invalid data: 'close' required")
        
        close = data['close']
        deltas = np.diff(close)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.convolve(gains, np.ones(self.period)/self.period, mode='valid')
        avg_loss = np.convolve(losses, np.ones(self.period)/self.period, mode='valid')
        
        # Calculate RS and RSI
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        
        # Pad with NaN
        result = np.full(len(close), np.nan)
        result[self.period:] = rsi
        
        return {"rsi": result}


class MACD(BaseIndicator):
    """Moving Average Convergence Divergence indicator"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(
            name="MACD",
            category=IndicatorCategory.MOMENTUM,
            description="Moving Average Convergence Divergence"
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.parameters = {
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period
        }
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate MACD"""
        if not self.validate_data(data):
            raise ValueError("Invalid data: 'close' required")
        
        close = data['close']
        
        # Calculate fast and slow EMAs
        fast_ema = ExponentialMovingAverage(self.fast_period).calculate(data)["ema"]
        slow_ema = ExponentialMovingAverage(self.slow_period).calculate(data)["ema"]
        
        # MACD line
        macd_line = fast_ema - slow_ema
        
        # Signal line (EMA of MACD)
        signal_ema = ExponentialMovingAverage(self.signal_period)
        signal_line = signal_ema.calculate({"close": macd_line})["ema"]
        
        # Histogram
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }


class BollingerBands(BaseIndicator):
    """Bollinger Bands indicator"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(
            name="BBands",
            category=IndicatorCategory.VOLATILITY,
            description=f"Bollinger Bands ({period} period, {std_dev} std)"
        )
        self.period = period
        self.std_dev = std_dev
        self.parameters = {"period": period, "std_dev": std_dev}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate Bollinger Bands"""
        if not self.validate_data(data):
            raise ValueError("Invalid data: 'close' required")
        
        close = data['close']
        
        # Middle band (SMA)
        sma = MovingAverage(self.period).calculate(data)["sma"]
        
        # Calculate rolling standard deviation
        std = np.zeros(len(close))
        for i in range(self.period - 1, len(close)):
            std[i] = np.std(close[i - self.period + 1:i + 1])
        
        # Upper and lower bands
        upper = sma + (self.std_dev * std)
        lower = sma - (self.std_dev * std)
        
        return {
            "upper": upper,
            "middle": sma,
            "lower": lower
        }


class ATR(BaseIndicator):
    """Average True Range indicator"""
    
    def __init__(self, period: int = 14):
        super().__init__(
            name="ATR",
            category=IndicatorCategory.VOLATILITY,
            description=f"Average True Range ({period} period)"
        )
        self.period = period
        self.parameters = {"period": period}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate ATR"""
        required = ['high', 'low', 'close']
        if not all(field in data for field in required):
            raise ValueError("Invalid data: 'high', 'low', 'close' required")
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        # True Range calculation
        tr = np.zeros(len(close))
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        # Average True Range (EMA of TR)
        atr = np.zeros(len(tr))
        atr[:self.period] = np.nan
        atr[self.period-1] = np.mean(tr[:self.period])
        
        alpha = 1 / self.period
        for i in range(self.period, len(tr)):
            atr[i] = alpha * tr[i] + (1 - alpha) * atr[i-1]
        
        return {"atr": atr}


class CustomIndicator(BaseIndicator):
    """User-defined custom indicator"""
    
    def __init__(
        self,
        name: str,
        calculate_fn: Callable[[Dict[str, np.ndarray]], Dict[str, np.ndarray]],
        description: str = "Custom indicator",
        parameters: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            name=name,
            category=IndicatorCategory.CUSTOM,
            description=description
        )
        self.calculate_fn = calculate_fn
        self.parameters = parameters or {}
    
    def calculate(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate custom indicator"""
        return self.calculate_fn(data)


class IndicatorRegistry:
    """Registry for managing indicators"""
    
    def __init__(self):
        self.indicators: Dict[str, BaseIndicator] = {}
        self._register_builtin_indicators()
    
    def _register_builtin_indicators(self):
        """Register built-in indicators"""
        self.register("sma", MovingAverage)
        self.register("ema", ExponentialMovingAverage)
        self.register("rsi", RSI)
        self.register("macd", MACD)
        self.register("bbands", BollingerBands)
        self.register("atr", ATR)
    
    def register(self, key: str, indicator_class: type):
        """Register an indicator class"""
        self.indicators[key] = indicator_class
        logger.info(f"Registered indicator: {key}")
    
    def register_custom(self, name: str, calculate_fn: Callable, description: str = ""):
        """Register a custom indicator function"""
        indicator = CustomIndicator(name, calculate_fn, description)
        self.indicators[name.lower()] = lambda **kwargs: indicator
        logger.info(f"Registered custom indicator: {name}")
    
    def get(self, key: str, **kwargs) -> BaseIndicator:
        """Get an indicator instance"""
        if key not in self.indicators:
            raise ValueError(f"Unknown indicator: {key}")
        
        indicator_class = self.indicators[key]
        return indicator_class(**kwargs)
    
    def list_indicators(self) -> List[Dict[str, Any]]:
        """List all registered indicators"""
        return [
            {
                "key": key,
                "name": indicator.__name__ if hasattr(indicator, '__name__') else key,
                "description": "Technical indicator"
            }
            for key, indicator in self.indicators.items()
        ]


# Global indicator registry
indicator_registry = IndicatorRegistry()


def calculate_indicator(
    indicator_name: str,
    data: Dict[str, np.ndarray],
    **params
) -> Dict[str, np.ndarray]:
    """
    Calculate an indicator by name
    
    Args:
        indicator_name: Name of the indicator (e.g., 'sma', 'rsi')
        data: Price data dictionary
        **params: Indicator parameters
    
    Returns:
        Dictionary with indicator outputs
    """
    indicator = indicator_registry.get(indicator_name.lower(), **params)
    return indicator.calculate(data)


def calculate_multiple_indicators(
    indicator_specs: List[Dict[str, Any]],
    data: Dict[str, np.ndarray]
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Calculate multiple indicators
    
    Args:
        indicator_specs: List of indicator specifications
            Example: [{"name": "sma", "params": {"period": 20}}]
        data: Price data dictionary
    
    Returns:
        Dictionary mapping indicator names to their outputs
    """
    results = {}
    
    for spec in indicator_specs:
        name = spec.get("name")
        params = spec.get("params", {})
        
        try:
            result = calculate_indicator(name, data, **params)
            results[name] = result
        except Exception as e:
            logger.error(f"Error calculating {name}: {e}")
            results[name] = {"error": str(e)}
    
    return results
