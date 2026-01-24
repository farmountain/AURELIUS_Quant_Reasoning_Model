"""Command-line interface for AURELIUS orchestrator."""

import sys
from pathlib import Path
import click

from aureus.orchestrator import Orchestrator


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """AURELIUS Quant Reasoning Model Orchestrator.
    
    An Evidence-Gated Intelligence Engine for Quant Reasoning.
    """
    pass


@cli.command()
@click.option(
    "--goal",
    required=True,
    help='Goal description (e.g., "design a trend strategy under DD<10%")',
)
@click.option(
    "--data",
    required=True,
    type=click.Path(exists=True),
    help="Path to market data parquet file",
)
@click.option(
    "--max-drawdown",
    default=0.10,
    type=float,
    help="Maximum allowed drawdown (default: 0.10 = 10%)",
)
@click.option(
    "--strict/--no-strict",
    default=True,
    help="Enable strict mode (artifact ID-only responses)",
)
@click.option(
    "--rust-cli",
    type=click.Path(exists=True),
    help="Path to Rust CLI binary (auto-detected if not provided)",
)
@click.option(
    "--hipcortex-cli",
    type=click.Path(exists=True),
    help="Path to HipCortex CLI binary (auto-detected if not provided)",
)
def run(
    goal: str,
    data: str,
    max_drawdown: float,
    strict: bool,
    rust_cli: str,
    hipcortex_cli: str,
) -> None:
    """Run a goal using the orchestrator.
    
    Example:
        aureus run --goal "design a trend strategy under DD<10%" --data examples/data.parquet
    """
    # Create orchestrator
    rust_cli_path = Path(rust_cli) if rust_cli else None
    hipcortex_cli_path = Path(hipcortex_cli) if hipcortex_cli else None
    
    orchestrator = Orchestrator(
        rust_cli_path=rust_cli_path,
        hipcortex_cli_path=hipcortex_cli_path,
        strict_mode=strict,
        max_drawdown_limit=max_drawdown,
    )
    
    # Run goal
    result = orchestrator.run_goal(goal, data)
    
    # Handle result
    if result["success"]:
        click.echo("\n" + "=" * 60)
        click.echo("✓ Goal completed successfully!")
        click.echo("=" * 60)
        
        if "artifact_id" in result:
            click.echo(f"\nArtifact ID: {result['artifact_id']}")
        
        if "stats" in result:
            stats = result["stats"]
            click.echo(f"\nFinal Statistics:")
            click.echo(f"  Total Return: {stats.get('total_return', 0)*100:.2f}%")
            click.echo(f"  Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}")
            click.echo(f"  Max Drawdown: {stats.get('max_drawdown', 0)*100:.2f}%")
        
        sys.exit(0)
    else:
        click.echo("\n" + "=" * 60)
        click.echo("✗ Goal failed")
        click.echo("=" * 60)
        
        if "error" in result:
            click.echo(f"\nError: {result['error']}")
        
        if "repair_plan" in result:
            plan = result["repair_plan"]
            click.echo(f"\nRepair plan generated:")
            click.echo(f"  Type: {plan.failure_type}")
            click.echo(f"  Description: {plan.description}")
            click.echo(f"\nSuggested actions:")
            for action in plan.actions:
                click.echo(f"  - {action}")
        
        sys.exit(1)


@cli.command()
def validate() -> None:
    """Validate the installation and check for required binaries."""
    click.echo("Validating AURELIUS installation...")
    
    try:
        from aureus.tools.rust_wrapper import RustEngineWrapper
        
        wrapper = RustEngineWrapper()
        click.echo(f"✓ Rust CLI found: {wrapper.rust_cli_path}")
        
        try:
            click.echo(f"✓ HipCortex CLI found: {wrapper.hipcortex_cli_path}")
        except RuntimeError:
            click.echo("✗ HipCortex CLI not found (optional)")
        
        click.echo("\n✓ Installation valid")
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"\n✗ Validation failed: {e}")
        click.echo("\nPlease build the Rust binaries:")
        click.echo("  cargo build --release")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
