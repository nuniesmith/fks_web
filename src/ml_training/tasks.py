"""
Celery tasks for automated ML model training and retraining.

Scheduled tasks for:
- Daily model retraining
- Model evaluation and comparison
- Model deployment automation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from celery import shared_task

logger = logging.getLogger(__name__)

# Service URLs
TRAINING_SERVICE_URL = "http://fks-training:8005"
MLFLOW_TRACKING_URI = "http://localhost:5000"


@shared_task(name="ml_training.retrain_model")
def retrain_model(
    model_name: str = "lstm_price_forecast",
    symbol: str = "BTC/USDT",
    data_path: Optional[str] = None,
    **kwargs,
) -> Dict:
    """
    Retrain an ML model with latest data.

    Args:
        model_name: Name of the model to retrain
        symbol: Trading symbol
        data_path: Optional path to data file
        **kwargs: Additional training parameters

    Returns:
        Dictionary with training results
    """
    try:
        logger.info(f"Starting retraining for {model_name} on {symbol}")

        # Call training service or run MLflow project
        # Option 1: Call training service API
        # Option 2: Run MLflow project directly

        # For now, use MLflow CLI via subprocess
        import subprocess
        import os

        training_dir = "/app"  # Adjust based on your setup

        # Build MLflow run command
        cmd = [
            "mlflow",
            "run",
            training_dir,
            "-e",
            "train",
            "-P",
            f"model_name={model_name}",
            "-P",
            f"symbol={symbol}",
        ]

        if data_path:
            cmd.extend(["-P", f"data_path={data_path}"])

        # Add additional parameters
        for key, value in kwargs.items():
            cmd.extend(["-P", f"{key}={value}"])

        # Run training
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=training_dir,
        )

        if result.returncode == 0:
            logger.info(f"Model {model_name} retrained successfully")
            return {
                "status": "success",
                "model_name": model_name,
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            logger.error(f"Training failed: {result.stderr}")
            return {
                "status": "failed",
                "error": result.stderr,
                "model_name": model_name,
            }

    except Exception as e:
        logger.error(f"Retraining task failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "model_name": model_name,
        }


@shared_task(name="ml_training.evaluate_model")
def evaluate_model(
    model_name: str,
    model_version: str = "latest",
    test_data_path: Optional[str] = None,
) -> Dict:
    """
    Evaluate a trained model on test data.

    Args:
        model_name: Name of the model
        model_version: Model version to evaluate
        test_data_path: Path to test data

    Returns:
        Dictionary with evaluation metrics
    """
    try:
        logger.info(f"Evaluating model {model_name} version {model_version}")

        # Run MLflow evaluate entry point
        import subprocess

        training_dir = "/app"
        cmd = [
            "mlflow",
            "run",
            training_dir,
            "-e",
            "evaluate",
            "-P",
            f"model_path=models:/{model_name}/{model_version}",
        ]

        if test_data_path:
            cmd.extend(["-P", f"test_data_path={test_data_path}"])

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=training_dir)

        if result.returncode == 0:
            # Parse metrics from output (simplified)
            return {
                "status": "success",
                "model_name": model_name,
                "model_version": model_version,
                "metrics": {},  # Would parse from MLflow
            }
        else:
            return {
                "status": "failed",
                "error": result.stderr,
            }

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(name="ml_training.compare_models")
def compare_models(
    model_name: str,
    versions: List[str],
    test_data_path: Optional[str] = None,
) -> Dict:
    """
    Compare multiple model versions.

    Args:
        model_name: Name of the model
        versions: List of versions to compare
        test_data_path: Path to test data

    Returns:
        Dictionary with comparison results
    """
    try:
        logger.info(f"Comparing {len(versions)} versions of {model_name}")

        results = []
        for version in versions:
            eval_result = evaluate_model(model_name, version, test_data_path)
            results.append(
                {
                    "version": version,
                    "metrics": eval_result.get("metrics", {}),
                }
            )

        # Find best version (simplified - would use actual metrics)
        best_version = versions[0]  # Placeholder

        return {
            "status": "success",
            "model_name": model_name,
            "comparisons": results,
            "best_version": best_version,
        }

    except Exception as e:
        logger.error(f"Model comparison failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(name="ml_training.promote_model")
def promote_model(
    model_name: str,
    version: str,
    target_stage: str = "production",
) -> Dict:
    """
    Promote a model version to a target stage.

    Args:
        model_name: Name of the model
        version: Model version to promote
        target_stage: Target stage (staging, production)

    Returns:
        Dictionary with promotion result
    """
    try:
        logger.info(f"Promoting {model_name} version {version} to {target_stage}")

        import subprocess

        training_dir = "/app"
        cmd = [
            "mlflow",
            "run",
            training_dir,
            "-e",
            "deploy",
            "-P",
            f"model_uri=models:/{model_name}/{version}",
            "-P",
            f"model_name={model_name}",
            "-P",
            f"stage={target_stage}",
            "-P",
            "action=promote",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=training_dir)

        if result.returncode == 0:
            return {
                "status": "success",
                "model_name": model_name,
                "version": version,
                "stage": target_stage,
            }
        else:
            return {
                "status": "failed",
                "error": result.stderr,
            }

    except Exception as e:
        logger.error(f"Model promotion failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(name="ml_training.daily_model_update")
def daily_model_update(symbols: Optional[List[str]] = None) -> Dict:
    """
    Daily task to retrain and update models for specified symbols.

    Args:
        symbols: List of symbols to update (default: common crypto pairs)

    Returns:
        Dictionary with update results
    """
    if symbols is None:
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]

    results = []
    for symbol in symbols:
        result = retrain_model.delay(
            model_name="lstm_price_forecast",
            symbol=symbol,
        )
        results.append({"symbol": symbol, "task_id": result.id})

    return {
        "status": "started",
        "symbols": symbols,
        "tasks": results,
        "timestamp": datetime.utcnow().isoformat(),
    }

