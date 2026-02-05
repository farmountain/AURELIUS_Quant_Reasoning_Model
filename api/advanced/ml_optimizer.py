"""
Machine Learning-Based Strategy Optimization
Uses Optuna for hyperparameter optimization with walk-forward validation
"""
import optuna
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of hyperparameter optimization"""
    best_params: Dict[str, Any]
    best_value: float
    optimization_history: List[Dict[str, Any]]
    study_name: str
    n_trials: int
    optimization_time: float


class StrategyOptimizer:
    """
    ML-based strategy parameter optimization using Optuna
    Implements walk-forward optimization with cross-validation
    """
    
    def __init__(
        self,
        objective_metric: str = "sharpe_ratio",
        n_trials: int = 100,
        n_jobs: int = 1,
        sampler: str = "tpe"
    ):
        """
        Initialize optimizer
        
        Args:
            objective_metric: Metric to optimize (sharpe_ratio, sortino_ratio, calmar_ratio, total_return)
            n_trials: Number of optimization trials
            n_jobs: Number of parallel jobs (-1 for all cores)
            sampler: Sampler algorithm (tpe, random, cmaes)
        """
        self.objective_metric = objective_metric
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self.sampler = sampler
    
    def optimize(
        self,
        backtest_function: Callable,
        param_space: Dict[str, Dict[str, Any]],
        data: Any,
        study_name: Optional[str] = None
    ) -> OptimizationResult:
        """
        Optimize strategy parameters
        
        Args:
            backtest_function: Function that takes params and data, returns metrics dict
            param_space: Parameter space definition
            data: Data to use for backtesting
            study_name: Optional name for the study
        
        Returns:
            OptimizationResult with best parameters and history
        """
        start_time = datetime.now()
        
        if study_name is None:
            study_name = f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create sampler
        if self.sampler == "tpe":
            sampler = optuna.samplers.TPESampler()
        elif self.sampler == "cmaes":
            sampler = optuna.samplers.CmaEsSampler()
        else:
            sampler = optuna.samplers.RandomSampler()
        
        # Create study
        study = optuna.create_study(
            study_name=study_name,
            direction="maximize",
            sampler=sampler
        )
        
        # Define objective function
        def objective(trial):
            # Sample parameters
            params = self._sample_params(trial, param_space)
            
            try:
                # Run backtest
                result = backtest_function(params, data)
                
                # Get objective value
                if self.objective_metric not in result:
                    logger.warning(f"Metric {self.objective_metric} not in result, using 0")
                    return 0.0
                
                value = result[self.objective_metric]
                
                # Report intermediate value
                trial.report(value, 0)
                
                return value
            except Exception as e:
                logger.error(f"Error in trial {trial.number}: {str(e)}")
                return float('-inf')
        
        # Run optimization
        study.optimize(
            objective,
            n_trials=self.n_trials,
            n_jobs=self.n_jobs,
            show_progress_bar=True
        )
        
        optimization_time = (datetime.now() - start_time).total_seconds()
        
        # Extract optimization history
        history = []
        for trial in study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                history.append({
                    "trial": trial.number,
                    "value": trial.value,
                    "params": trial.params,
                    "datetime": trial.datetime_start.isoformat() if trial.datetime_start else None
                })
        
        return OptimizationResult(
            best_params=study.best_params,
            best_value=study.best_value,
            optimization_history=history,
            study_name=study_name,
            n_trials=len(study.trials),
            optimization_time=optimization_time
        )
    
    def walk_forward_optimize(
        self,
        backtest_function: Callable,
        param_space: Dict[str, Dict[str, Any]],
        data: Any,
        n_splits: int = 5,
        train_size: float = 0.7
    ) -> Dict[str, Any]:
        """
        Walk-forward optimization with cross-validation
        
        Args:
            backtest_function: Function for backtesting
            param_space: Parameter space definition
            data: Full dataset
            n_splits: Number of walk-forward splits
            train_size: Fraction of data for training in each split
        
        Returns:
            Dictionary with results from all splits
        """
        results = []
        split_size = len(data) // n_splits
        
        for i in range(n_splits):
            logger.info(f"Walk-forward split {i+1}/{n_splits}")
            
            # Split data
            start_idx = i * split_size
            train_end_idx = start_idx + int(split_size * train_size)
            test_end_idx = start_idx + split_size
            
            train_data = data[start_idx:train_end_idx]
            test_data = data[train_end_idx:test_end_idx]
            
            # Optimize on training data
            def train_objective(params, _):
                return backtest_function(params, train_data)
            
            opt_result = self.optimize(
                train_objective,
                param_space,
                train_data,
                study_name=f"wf_split_{i}"
            )
            
            # Test on out-of-sample data
            test_result = backtest_function(opt_result.best_params, test_data)
            
            results.append({
                "split": i,
                "train_size": len(train_data),
                "test_size": len(test_data),
                "best_params": opt_result.best_params,
                "train_score": opt_result.best_value,
                "test_score": test_result.get(self.objective_metric, 0.0),
                "test_metrics": test_result
            })
        
        # Calculate aggregate statistics
        train_scores = [r["train_score"] for r in results]
        test_scores = [r["test_score"] for r in results]
        
        return {
            "splits": results,
            "aggregate": {
                "mean_train_score": np.mean(train_scores),
                "std_train_score": np.std(train_scores),
                "mean_test_score": np.mean(test_scores),
                "std_test_score": np.std(test_scores),
                "overfitting": np.mean(train_scores) - np.mean(test_scores)
            }
        }
    
    def _sample_params(self, trial: optuna.Trial, param_space: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Sample parameters from the search space"""
        params = {}
        
        for param_name, param_config in param_space.items():
            param_type = param_config.get("type")
            
            if param_type == "int":
                params[param_name] = trial.suggest_int(
                    param_name,
                    param_config["low"],
                    param_config["high"],
                    step=param_config.get("step", 1)
                )
            elif param_type == "float":
                if param_config.get("log", False):
                    params[param_name] = trial.suggest_float(
                        param_name,
                        param_config["low"],
                        param_config["high"],
                        log=True
                    )
                else:
                    params[param_name] = trial.suggest_float(
                        param_name,
                        param_config["low"],
                        param_config["high"],
                        step=param_config.get("step")
                    )
            elif param_type == "categorical":
                params[param_name] = trial.suggest_categorical(
                    param_name,
                    param_config["choices"]
                )
            else:
                logger.warning(f"Unknown parameter type: {param_type}")
        
        return params


class EnsembleOptimizer:
    """
    Ensemble optimization combining multiple optimization strategies
    """
    
    def __init__(self, optimizers: List[StrategyOptimizer]):
        """
        Initialize ensemble optimizer
        
        Args:
            optimizers: List of StrategyOptimizer instances
        """
        self.optimizers = optimizers
    
    def optimize(
        self,
        backtest_function: Callable,
        param_space: Dict[str, Dict[str, Any]],
        data: Any
    ) -> Dict[str, Any]:
        """
        Run all optimizers and combine results
        
        Returns:
            Dictionary with results from all optimizers and consensus
        """
        results = []
        
        for i, optimizer in enumerate(self.optimizers):
            logger.info(f"Running optimizer {i+1}/{len(self.optimizers)}")
            result = optimizer.optimize(
                backtest_function,
                param_space,
                data,
                study_name=f"ensemble_{i}"
            )
            results.append(result)
        
        # Find consensus parameters (median or mode)
        all_params = [r.best_params for r in results]
        consensus_params = self._calculate_consensus(all_params)
        
        # Test consensus
        consensus_result = backtest_function(consensus_params, data)
        
        return {
            "individual_results": [
                {
                    "best_params": r.best_params,
                    "best_value": r.best_value,
                    "n_trials": r.n_trials
                }
                for r in results
            ],
            "consensus_params": consensus_params,
            "consensus_score": consensus_result.get("sharpe_ratio", 0.0),
            "consensus_metrics": consensus_result
        }
    
    def _calculate_consensus(self, all_params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus parameters from multiple optimization runs"""
        consensus = {}
        
        # Get all parameter names
        param_names = set()
        for params in all_params:
            param_names.update(params.keys())
        
        for param_name in param_names:
            values = [p[param_name] for p in all_params if param_name in p]
            
            # For numeric parameters, use median
            if all(isinstance(v, (int, float)) for v in values):
                consensus[param_name] = np.median(values)
                if all(isinstance(v, int) for v in values):
                    consensus[param_name] = int(consensus[param_name])
            # For categorical, use mode
            else:
                from collections import Counter
                consensus[param_name] = Counter(values).most_common(1)[0][0]
        
        return consensus


# Example parameter space definitions
EXAMPLE_PARAM_SPACES = {
    "moving_average_crossover": {
        "fast_period": {"type": "int", "low": 5, "high": 50, "step": 5},
        "slow_period": {"type": "int", "low": 20, "high": 200, "step": 10},
        "signal_threshold": {"type": "float", "low": 0.0, "high": 0.05, "step": 0.01}
    },
    "mean_reversion": {
        "lookback_period": {"type": "int", "low": 10, "high": 100, "step": 5},
        "entry_threshold": {"type": "float", "low": 1.0, "high": 3.0, "step": 0.1},
        "exit_threshold": {"type": "float", "low": 0.0, "high": 1.0, "step": 0.1}
    },
    "portfolio": {
        "rebalance_frequency": {"type": "categorical", "choices": ["daily", "weekly", "monthly"]},
        "risk_target": {"type": "float", "low": 0.05, "high": 0.30, "step": 0.05},
        "max_position_size": {"type": "float", "low": 0.05, "high": 0.30, "step": 0.05}
    }
}
