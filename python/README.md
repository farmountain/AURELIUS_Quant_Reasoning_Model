# AURELIUS Python Orchestrator

Python orchestrator for the AURELIUS Quant Reasoning Model that controls the Rust engine via subprocess with FSM-based tool sequencing, dual-loop evidence gates, and reflexion loops.

## Features

- **Tool API Wrappers**: JSON schema-validated wrappers for Rust CLI commands
- **Goal-Guard FSM**: State machine that enforces valid tool call sequences
- **Dual-Loop Evidence Gates**:
  - Dev Gate: Tests, determinism checks, linting
  - Product Gate: CRV verification, walk-forward validation, stress testing
- **Reflexion Loop**: Automatic failure analysis and repair plan generation
- **Strict Mode**: Enforces artifact ID-only responses for reproducibility

## Installation

```bash
# From the python directory
cd python
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Prerequisites

The Rust binaries must be built before using the orchestrator:

```bash
# From repository root
cargo build --release
```

## Usage

### Command Line

```bash
# Run a goal
aureus run --goal "design a trend strategy under DD<10%" --data ../examples/data.parquet

# Validate installation
aureus validate
```

### Python API

```python
from aureus.orchestrator import Orchestrator

# Create orchestrator
orchestrator = Orchestrator(
    strict_mode=True,
    max_drawdown_limit=0.10,
)

# Run a goal
result = orchestrator.run_goal(
    goal="design a trend strategy under DD<10%",
    data_path="examples/data.parquet",
)

if result["success"]:
    print(f"Artifact ID: {result['artifact_id']}")
    print(f"Stats: {result['stats']}")
```

## Architecture

### FSM States

- `INIT`: Initial state
- `STRATEGY_DESIGN`: Strategy generation phase
- `BACKTEST_COMPLETE`: Backtest completed
- `DEV_GATE`: Running development checks
- `DEV_GATE_PASSED`: All dev checks passed
- `PRODUCT_GATE`: Running product checks
- `PRODUCT_GATE_PASSED`: All product checks passed
- `COMMITTED`: Artifact committed to HipCortex
- `REFLEXION`: Error recovery and repair
- `ERROR`: Unrecoverable error

### Tool Sequences

Valid tool sequences are enforced by the FSM:

1. `GENERATE_STRATEGY` → `BACKTEST` → `RUN_TESTS` → Dev Gate
2. Dev Gate → `CRV_VERIFY` → Product Gate
3. Product Gate → `HIPCORTEX_COMMIT` → `COMMITTED`

Invalid sequences are blocked (e.g., cannot run CRV before dev gate passes).

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aureus --cov-report=html

# Run specific test file
pytest tests/test_fsm.py
```

## Example Goals

- "design a trend strategy under DD<10%"
- "create a momentum strategy with Sharpe > 1.5"
- "build a mean reversion strategy for low volatility regimes"

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black aureus/ tests/

# Type check
mypy aureus/

# Run linter
pylint aureus/
```

## License

Apache License 2.0 - see [../LICENSE](../LICENSE) for details.
