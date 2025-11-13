"""
Finlab data downloader with retry logic and rate limit handling.

Provides robust data downloading from Finlab API with exponential backoff
retry mechanism and comprehensive error handling.
"""

import time
from queue import Queue
from concurrent.futures import Future
from threading import Thread, Lock
from typing import Optional, Dict

import pandas as pd

from src.utils.exceptions import DataError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FinlabDownloader:
    """
    Download financial data from Finlab API with retry logic.

    Implements exponential backoff retry strategy for handling transient
    failures and rate limiting. Integrates with finlab.data.get() API.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 4)
        base_delay: Initial delay in seconds for exponential backoff (default: 5)
        max_delay: Maximum delay between retries in seconds (default: 60)
    """

    def __init__(
        self,
        max_retries: int = 4,
        base_delay: float = 5.0,
        max_delay: float = 60.0,
        queue_timeout: float = 300.0
    ) -> None:
        """
        Initialize FinlabDownloader with retry and queue configuration.

        Args:
            max_retries: Maximum retry attempts (default: 4)
            base_delay: Initial retry delay in seconds (default: 5.0)
            max_delay: Maximum retry delay cap in seconds (default: 60.0)
            queue_timeout: Maximum wait time for queued requests in seconds (default: 300.0)

        Raises:
            ValueError: If parameters are invalid (negative values, etc.)
        """
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if queue_timeout <= 0:
            raise ValueError("queue_timeout must be positive")

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.queue_timeout = queue_timeout

        # Request queue infrastructure
        self._request_queue: Queue[tuple[str, Future[pd.DataFrame]]] = Queue()
        self._rate_limited: bool = False
        self._rate_limit_lock: Lock = Lock()

        # Start background queue processor
        self._queue_processor = Thread(
            target=self._process_queue,
            daemon=True,
            name="finlab-queue-processor"
        )
        self._queue_processor.start()

        logger.info(
            f"Initialized FinlabDownloader: "
            f"max_retries={max_retries}, "
            f"base_delay={base_delay}s, "
            f"max_delay={max_delay}s, "
            f"queue_timeout={queue_timeout}s"
        )

    def _process_queue(self) -> None:
        """
        Background thread to process queued requests during rate limits.

        Continuously processes requests from the queue, downloading data
        and returning results via Futures. Deactivates rate limit flag
        when queue is empty and processing succeeds.
        """
        logger.info("Queue processor thread started")

        while True:
            # Wait for queued request
            dataset, future = self._request_queue.get()

            try:
                logger.info(f"Processing queued request: {dataset}")

                # Download with internal retry logic
                data = self._download_with_retry_internal(dataset)

                # Set result on Future
                future.set_result(data)

                logger.info(f"Queued request completed: {dataset}")

                # Check if we can deactivate rate limit mode
                with self._rate_limit_lock:
                    if self._request_queue.empty():
                        self._rate_limited = False
                        logger.info(
                            "Rate limit deactivated - queue empty, "
                            "normal operations resumed"
                        )

            except Exception as e:
                # Set exception on Future
                future.set_exception(e)
                logger.error(f"Queued request failed: {dataset}: {e}")

            finally:
                # Mark task as done
                self._request_queue.task_done()

    def _download_with_retry_internal(self, dataset: str) -> pd.DataFrame:
        """
        Internal download method with retry logic (used by queue processor).

        Args:
            dataset: Dataset identifier to download

        Returns:
            Downloaded DataFrame

        Raises:
            DataError: If all retry attempts fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Internal download attempt {attempt + 1}/{self.max_retries + 1} "
                    f"for dataset: {dataset}"
                )

                data = self._download_from_finlab(dataset)

                logger.info(
                    f"Internal download successful: {dataset} "
                    f"(shape: {data.shape}, attempt: {attempt + 1})"
                )
                return data

            except Exception as e:
                last_error = e
                error_msg = str(e)

                # Check if this is a rate limit error
                is_rate_limit = self._is_rate_limit_error(e)

                if attempt < self.max_retries:
                    # Calculate exponential backoff delay
                    delay = min(
                        self.base_delay * (2 ** attempt),
                        self.max_delay
                    )

                    if is_rate_limit:
                        logger.warning(
                            f"Rate limit in queue processor for: {dataset}. "
                            f"Retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{self.max_retries + 1})"
                        )
                    else:
                        logger.warning(
                            f"Internal download failed for: {dataset}. "
                            f"Error: {error_msg}. "
                            f"Retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{self.max_retries + 1})"
                        )

                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} internal download attempts failed "
                        f"for dataset: {dataset}. "
                        f"Final error: {error_msg}"
                    )

        # All retries exhausted
        error_message = (
            f"Failed to download dataset '{dataset}' "
            f"after {self.max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )
        raise DataError(error_message) from last_error

    def download_with_retry(self, dataset: str) -> pd.DataFrame:
        """
        Download dataset from Finlab API with exponential backoff retry and queue support.

        Implements intelligent request queueing during rate limits:
        - If rate limited: Queue request and wait for result via Future
        - If not rate limited: Download directly with retry logic
        - On rate limit detection: Activate queue mode for subsequent requests

        Retry strategy:
        - Attempt 1: Immediate
        - Attempt 2: 5s delay
        - Attempt 3: 10s delay
        - Attempt 4: 20s delay
        - Attempt 5: 40s delay (capped at max_delay)

        Args:
            dataset: Dataset identifier (e.g., "etl:broker_transactions:top15_buy")

        Returns:
            DataFrame containing the downloaded dataset

        Raises:
            DataError: If download fails after all retry attempts
            ValueError: If dataset identifier is empty or invalid format
            TimeoutError: If queued request exceeds queue_timeout
        """
        if not dataset or not isinstance(dataset, str):
            raise ValueError(
                f"Invalid dataset identifier: {dataset!r}. "
                f"Must be a non-empty string."
            )

        # Check if currently in rate-limited mode
        with self._rate_limit_lock:
            if self._rate_limited:
                logger.info(
                    f"System is rate limited - queueing request: {dataset}"
                )

                # Queue this request
                future: Future[pd.DataFrame] = Future()
                self._request_queue.put((dataset, future))

                logger.info(
                    f"Request queued (position: {self._request_queue.qsize()}): {dataset}"
                )

                try:
                    # Wait for result with timeout
                    result: pd.DataFrame = future.result(timeout=self.queue_timeout)
                    logger.info(f"Queued request completed: {dataset}")
                    return result
                except TimeoutError:
                    error_msg = (
                        f"Queued request timed out after {self.queue_timeout}s: {dataset}"
                    )
                    logger.error(error_msg)
                    raise DataError(error_msg)

        # Not rate limited - proceed with normal download
        logger.info(f"Starting download for dataset: {dataset}")

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                # Attempt download
                logger.debug(
                    f"Download attempt {attempt + 1}/{self.max_retries + 1} "
                    f"for dataset: {dataset}"
                )

                data = self._download_from_finlab(dataset)

                logger.info(
                    f"Successfully downloaded dataset: {dataset} "
                    f"(shape: {data.shape}, attempt: {attempt + 1})"
                )
                return data

            except Exception as e:
                last_error = e
                error_msg = str(e)

                # Check if this is a rate limit error
                is_rate_limit = self._is_rate_limit_error(e)

                if is_rate_limit:
                    # Activate rate limit mode
                    with self._rate_limit_lock:
                        if not self._rate_limited:
                            self._rate_limited = True
                            logger.warning(
                                "Rate limit detected - activating queue mode. "
                                "Subsequent requests will be queued."
                            )

                    # Queue this request
                    future_rl: Future[pd.DataFrame] = Future()
                    self._request_queue.put((dataset, future_rl))

                    logger.info(f"Request queued due to rate limit: {dataset}")

                    try:
                        # Wait for result with timeout
                        result_rl: pd.DataFrame = future_rl.result(timeout=self.queue_timeout)
                        logger.info(f"Queued request completed: {dataset}")
                        return result_rl
                    except TimeoutError:
                        error_msg = (
                            f"Queued request timed out after {self.queue_timeout}s: {dataset}"
                        )
                        logger.error(error_msg)
                        raise DataError(error_msg)

                elif attempt < self.max_retries:
                    # Non-rate-limit error - retry with backoff
                    delay = min(
                        self.base_delay * (2 ** attempt),
                        self.max_delay
                    )

                    logger.warning(
                        f"Download failed for dataset: {dataset}. "
                        f"Error: {error_msg}. "
                        f"Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )

                    time.sleep(delay)
                else:
                    # Final attempt failed
                    logger.error(
                        f"All {self.max_retries + 1} download attempts failed "
                        f"for dataset: {dataset}. "
                        f"Final error: {error_msg}"
                    )

        # All retries exhausted
        error_message = (
            f"Failed to download dataset '{dataset}' "
            f"after {self.max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )
        raise DataError(error_message) from last_error

    def _download_from_finlab(self, dataset: str) -> pd.DataFrame:
        """
        Internal method to download data from Finlab API.

        Args:
            dataset: Dataset identifier for Finlab API

        Returns:
            DataFrame containing the dataset

        Raises:
            Exception: Any exception from finlab.data.get()
        """
        try:
            # Import finlab here to allow for mocking in tests
            from finlab import data  # type: ignore[import-untyped]

            logger.debug(f"Calling finlab.data.get('{dataset}')")
            result = data.get(dataset)

            # Validate result is a DataFrame
            if not isinstance(result, pd.DataFrame):
                raise DataError(
                    f"Expected DataFrame from Finlab API, "
                    f"got {type(result).__name__}"
                )

            if result.empty:
                logger.warning(f"Downloaded empty DataFrame for dataset: {dataset}")

            return result

        except ImportError as e:
            raise DataError(
                f"Failed to import finlab package. "
                f"Ensure 'finlab' is installed: {e}"
            ) from e
        except Exception:
            # Re-raise for retry logic to handle
            raise

    def get_queue_metrics(self) -> Dict[str, int | bool]:
        """
        Get current queue metrics for monitoring.

        Returns:
            Dictionary containing queue metrics:
                - queue_size: Number of pending requests
                - rate_limited: Whether system is in rate-limited mode
                - queue_processor_alive: Whether queue processor thread is running
        """
        with self._rate_limit_lock:
            return {
                "queue_size": self._request_queue.qsize(),
                "rate_limited": self._rate_limited,
                "queue_processor_alive": self._queue_processor.is_alive()
            }

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """
        Check if error indicates API rate limiting.

        Args:
            error: Exception to check

        Returns:
            True if error is likely due to rate limiting
        """
        error_str = str(error).lower()

        # Common rate limit indicators
        rate_limit_keywords = [
            "rate limit",
            "too many requests",
            "429",
            "quota exceeded",
            "throttle",
        ]

        return any(keyword in error_str for keyword in rate_limit_keywords)


__all__ = ["FinlabDownloader"]
