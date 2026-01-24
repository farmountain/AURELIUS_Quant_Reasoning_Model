"""Tests for tool schemas."""

import pytest
from pydantic import ValidationError
from aureus.tools.schemas import (
    ToolType,
    StrategyConfig,
    CostModelConfig,
    BacktestSpec,
    BacktestToolInput,
    ToolCall,
    ToolResult,
)


def test_strategy_config_valid():
    """Test valid strategy configuration."""
    config = StrategyConfig(
        type="ts_momentum",
        symbol="AAPL",
        lookback=20,
        vol_target=0.15,
        vol_lookback=20,
    )
    
    assert config.type == "ts_momentum"
    assert config.symbol == "AAPL"
    assert config.lookback == 20


def test_strategy_config_invalid_lookback():
    """Test strategy config rejects invalid lookback."""
    with pytest.raises(ValidationError):
        StrategyConfig(
            type="ts_momentum",
            symbol="AAPL",
            lookback=0,  # Must be >= 1
            vol_target=0.15,
            vol_lookback=20,
        )


def test_strategy_config_invalid_vol_target():
    """Test strategy config rejects invalid vol_target."""
    with pytest.raises(ValidationError):
        StrategyConfig(
            type="ts_momentum",
            symbol="AAPL",
            lookback=20,
            vol_target=1.5,  # Must be <= 1
            vol_lookback=20,
        )


def test_cost_model_config():
    """Test cost model configuration."""
    config = CostModelConfig(
        type="fixed_per_share",
        cost_per_share=0.005,
        minimum_commission=1.0,
    )
    
    assert config.type == "fixed_per_share"
    assert config.cost_per_share == 0.005


def test_backtest_spec():
    """Test backtest specification."""
    spec = BacktestSpec(
        initial_cash=100000.0,
        seed=42,
        strategy=StrategyConfig(
            type="ts_momentum",
            symbol="AAPL",
            lookback=20,
            vol_target=0.15,
            vol_lookback=20,
        ),
        cost_model=CostModelConfig(
            type="fixed_per_share",
            cost_per_share=0.005,
            minimum_commission=1.0,
        ),
    )
    
    assert spec.initial_cash == 100000.0
    assert spec.seed == 42


def test_backtest_tool_input():
    """Test backtest tool input."""
    input_data = BacktestToolInput(
        spec=BacktestSpec(
            initial_cash=100000.0,
            seed=42,
            strategy=StrategyConfig(
                type="ts_momentum",
                symbol="AAPL",
                lookback=20,
                vol_target=0.15,
                vol_lookback=20,
            ),
            cost_model=CostModelConfig(
                type="zero",
            ),
        ),
        data_path="/path/to/data.parquet",
        output_dir="/path/to/output",
    )
    
    assert input_data.data_path == "/path/to/data.parquet"


def test_tool_call():
    """Test tool call creation."""
    call = ToolCall(
        tool_type=ToolType.BACKTEST,
        parameters=BacktestToolInput(
            spec=BacktestSpec(
                initial_cash=100000.0,
                seed=42,
                strategy=StrategyConfig(
                    type="ts_momentum",
                    symbol="AAPL",
                    lookback=20,
                    vol_target=0.15,
                    vol_lookback=20,
                ),
                cost_model=CostModelConfig(type="zero"),
            ),
            data_path="/path/to/data.parquet",
            output_dir="/path/to/output",
        ),
    )
    
    assert call.tool_type == ToolType.BACKTEST


def test_tool_result_success():
    """Test successful tool result."""
    result = ToolResult(
        success=True,
        output={"key": "value"},
        artifact_id="test_id_123",
    )
    
    assert result.success
    assert result.output["key"] == "value"
    assert result.artifact_id == "test_id_123"
    assert "Success" in str(result)


def test_tool_result_failure():
    """Test failed tool result."""
    result = ToolResult(
        success=False,
        error="Something went wrong",
    )
    
    assert not result.success
    assert result.error == "Something went wrong"
    assert "Error" in str(result)


def test_tool_type_enum():
    """Test ToolType enum."""
    assert ToolType.BACKTEST == "backtest"
    assert ToolType.CRV_VERIFY == "crv_verify"
    assert ToolType.HIPCORTEX_COMMIT == "hipcortex_commit"
