"""
Performance and metrics logging module for APIWrapper calls.
Handles serializable JSON entries for monitoring API performance and enabling
future queue-based re-calling of API calls.
"""

import json
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="performance_metrics.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


class PerformanceLogger:
    """
    Logs API call performance metrics in JSON format for analysis and queue management.
    """

    def __init__(self, log_dir: str = "logs/metrics"):
        """
        Initialize the performance logger.

        Args:
            log_dir: Directory to store JSON log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def generate_log_id(self, timestamp: float = None) -> str:
        """
        Generate a unique identifier for a log entry.

        Args:
            timestamp: Unix timestamp (uses current time if None)

        Returns:
            Unique identifier string
        """
        if timestamp is None:
            timestamp = time.time()
        return str(timestamp).replace(".", "_")

    def create_base_entry(
        self,
        prompt: str,
        model: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create the base log entry structure.

        Args:
            prompt: The input prompt
            model: Model name used
            metadata: Optional metadata dictionary

        Returns:
            Base log entry dictionary
        """
        if metadata is None:
            metadata = {}

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt,
            "model": model,
            "metadata": metadata,
        }

    def log_success(
        self,
        log_entry: Dict[str, Any],
        response: str,
        latency_sec: float,
        log_id: str = None
    ) -> Dict[str, Any]:
        """
        Log a successful API call.

        Args:
            log_entry: Base log entry from create_base_entry
            response: The model's response text
            latency_sec: Time taken for the API call in seconds
            log_id: Optional custom log ID (generated if None)

        Returns:
            Complete log entry
        """
        if log_id is None:
            log_id = self.generate_log_id()

        complete_entry = log_entry.copy()
        complete_entry.update({
            "response": response,
            "latency_sec": round(latency_sec, 3),
            "status": "success",
            "log_id": log_id,
        })

        # Write to file
        self._write_log_file(log_id, complete_entry)

        # Log to Python logger
        logging.info(f"Success - {log_id}: {complete_entry}")

        return complete_entry

    def log_error(
        self,
        log_entry: Dict[str, Any],
        error: Exception,
        latency_sec: float,
        log_id: str = None
    ) -> Dict[str, Any]:
        """
        Log a failed API call.

        Args:
            log_entry: Base log entry from create_base_entry
            error: The exception that occurred
            latency_sec: Time taken before failure in seconds
            log_id: Optional custom log ID (generated if None)

        Returns:
            Complete error log entry
        """
        if log_id is None:
            log_id = self.generate_log_id()

        complete_entry = log_entry.copy()
        complete_entry.update({
            "error": str(error),
            "error_type": type(error).__name__,
            "latency_sec": round(latency_sec, 3),
            "status": "error",
            "log_id": log_id,
        })

        # Write to file
        self._write_log_file(log_id, complete_entry)

        # Log to Python logger
        logging.error(f"Error - {log_id}: {complete_entry}")

        return complete_entry

    def _write_log_file(self, log_id: str, entry: Dict[str, Any]) -> bool:
        """
        Write log entry to JSON file.

        Args:
            log_id: Unique identifier for the log
            entry: Complete log entry dictionary

        Returns:
            True if successful, False otherwise
        """
        filepath = os.path.join(self.log_dir, f"{log_id}.json")

        try:
            # Ensure the entry is JSON serializable
            json_str = json.dumps(entry)

            with open(filepath, "w") as f:
                f.write(json_str)
            return True

        except TypeError as e:
            logging.error(f"Serialization error for {log_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Could not write log file {filepath}: {e}")
            return False

    def read_log_entry(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a previously logged entry.

        Args:
            log_id: Unique identifier for the log

        Returns:
            Log entry dictionary or None if not found
        """
        filepath = os.path.join(self.log_dir, f"{log_id}.json")

        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Log file not found: {log_id}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Could not parse log file {log_id}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading log file {log_id}: {e}")
            return None

    def get_all_logs(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all logged entries.

        Returns:
            Dictionary mapping log_id to log entry
        """
        logs = {}

        if not os.path.exists(self.log_dir):
            return logs

        try:
            for filename in os.listdir(self.log_dir):
                if filename.endswith(".json"):
                    log_id = filename[:-5]  # Remove .json extension
                    entry = self.read_log_entry(log_id)
                    if entry:
                        logs[log_id] = entry
        except Exception as e:
            logging.error(f"Error reading logs directory: {e}")

        return logs

    def get_logs_by_status(self, status: str) -> Dict[str, Dict[str, Any]]:
        """
        Get logs filtered by status (success or error).

        Args:
            status: "success" or "error"

        Returns:
            Dictionary mapping log_id to matching log entries
        """
        all_logs = self.get_all_logs()
        return {log_id: entry for log_id, entry in all_logs.items()
                if entry.get("status") == status}

    def get_logs_by_model(self, model: str) -> Dict[str, Dict[str, Any]]:
        """
        Get logs filtered by model name.

        Args:
            model: Model name to filter by

        Returns:
            Dictionary mapping log_id to matching log entries
        """
        all_logs = self.get_all_logs()
        return {log_id: entry for log_id, entry in all_logs.items()
                if entry.get("model") == model}

    def get_performance_stats(self, model: str = None) -> Dict[str, Any]:
        """
        Calculate performance statistics for logged calls.

        Args:
            model: Optional model name to filter stats by

        Returns:
            Dictionary with performance statistics
        """
        logs = self.get_all_logs()

        if model:
            logs = {log_id: entry for log_id, entry in logs.items()
                    if entry.get("model") == model}

        if not logs:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_latency_sec": 0,
                "min_latency_sec": 0,
                "max_latency_sec": 0,
            }

        latencies = []
        successful = 0
        failed = 0

        for entry in logs.values():
            if entry.get("status") == "success":
                successful += 1
                latencies.append(entry.get("latency_sec", 0))
            elif entry.get("status") == "error":
                failed += 1

        return {
            "total_calls": len(logs),
            "successful_calls": successful,
            "failed_calls": failed,
            "success_rate": round(successful / len(logs) * 100, 2) if logs else 0,
            "avg_latency_sec": round(sum(latencies) / len(latencies), 3) if latencies else 0,
            "min_latency_sec": round(min(latencies), 3) if latencies else 0,
            "max_latency_sec": round(max(latencies), 3) if latencies else 0,
        }


# Global singleton instance for easy access
_performance_logger = None


def get_performance_logger(log_dir: str = "logs/metrics") -> PerformanceLogger:
    """
    Get or create the global performance logger instance.

    Args:
        log_dir: Directory for log files

    Returns:
        PerformanceLogger instance
    """
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger(log_dir)
    return _performance_logger
