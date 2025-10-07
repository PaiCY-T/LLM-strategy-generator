"""
Data freshness checking with bilingual messaging support.

Provides cache freshness validation with configurable thresholds and
bilingual (zh-TW/en-US) status messages.
"""

from datetime import datetime
from typing import Literal, Tuple

from src.data.cache import DataCache
from src.utils.exceptions import DataError
from src.utils.logger import get_logger

logger = get_logger(__name__)

Language = Literal["zh-TW", "en-US"]


class FreshnessChecker:
    """
    Check cached data freshness with bilingual messaging.

    Validates whether cached data meets freshness thresholds and provides
    human-readable status messages in Traditional Chinese (zh-TW) or
    English (en-US).

    Attributes:
        cache: DataCache instance for checking cache age
        max_age_days: Maximum age in days before data is considered stale
        language: Message language (zh-TW or en-US)
    """

    # Bilingual message templates
    MESSAGES = {
        "fresh": {
            "zh-TW": "資料新鮮（{days}天前）",
            "en-US": "Data is fresh ({days} days old)"
        },
        "stale": {
            "zh-TW": "資料過期（{days}天前，閾值：{threshold}天）",
            "en-US": "Data is stale ({days} days old, threshold: {threshold} days)"
        },
        "missing": {
            "zh-TW": "無快取資料",
            "en-US": "No cached data available"
        },
        "error": {
            "zh-TW": "檢查失敗：{error}",
            "en-US": "Check failed: {error}"
        }
    }

    def __init__(
        self,
        cache: DataCache,
        max_age_days: int = 7,
        language: Language = "en-US"
    ) -> None:
        """
        Initialize FreshnessChecker with cache and thresholds.

        Args:
            cache: DataCache instance for age checking
            max_age_days: Maximum age in days before stale (default: 7)
            language: Message language, zh-TW or en-US (default: en-US)

        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(cache, DataCache):
            raise ValueError(
                f"Invalid cache type: {type(cache).__name__}. "
                f"Expected DataCache instance."
            )

        if max_age_days < 0:
            raise ValueError(
                f"Invalid max_age_days: {max_age_days}. "
                f"Must be non-negative."
            )

        if language not in ("zh-TW", "en-US"):
            raise ValueError(
                f"Invalid language: {language!r}. "
                f"Must be 'zh-TW' or 'en-US'."
            )

        self.cache = cache
        self.max_age_days = max_age_days
        self.language = language

        logger.info(
            f"Initialized FreshnessChecker: "
            f"max_age_days={max_age_days}, language={language}"
        )

    def check_freshness(
        self,
        dataset: str
    ) -> Tuple[bool, datetime | None, str]:
        """
        Check if cached data meets freshness threshold.

        Args:
            dataset: Dataset identifier to check

        Returns:
            Tuple of (is_fresh, last_updated, status_message):
                - is_fresh: True if data age <= max_age_days
                - last_updated: Timestamp of cache file, None if not cached
                - status_message: Human-readable status in configured language

        Raises:
            ValueError: If dataset identifier is invalid
        """
        if not dataset or not isinstance(dataset, str):
            raise ValueError(
                f"Invalid dataset identifier: {dataset!r}. "
                f"Must be a non-empty string."
            )

        logger.debug(
            f"Checking freshness for dataset: {dataset} "
            f"(threshold: {self.max_age_days} days)"
        )

        try:
            # Get cache age from DataCache
            cache_age = self.cache.get_cache_age(dataset)

            if cache_age is None:
                # No cache exists
                message = self._get_message("missing")
                logger.info(
                    f"No cache found for dataset: {dataset}. "
                    f"Message: {message}"
                )
                return False, None, message

            # Calculate age in days
            age_days = cache_age.days

            # Calculate last updated timestamp
            last_updated = datetime.utcnow() - cache_age

            # Check freshness
            is_fresh = age_days <= self.max_age_days

            if is_fresh:
                message = self._get_message(
                    "fresh",
                    days=age_days
                )
                logger.info(
                    f"Dataset {dataset} is fresh: {age_days} days old. "
                    f"Message: {message}"
                )
            else:
                message = self._get_message(
                    "stale",
                    days=age_days,
                    threshold=self.max_age_days
                )
                logger.warning(
                    f"Dataset {dataset} is stale: {age_days} days old "
                    f"(threshold: {self.max_age_days} days). "
                    f"Message: {message}"
                )

            return is_fresh, last_updated, message

        except ValueError:
            # Re-raise validation errors
            raise
        except DataError as e:
            # Handle known cache-related errors
            error_str = str(e)
            message = self._get_message("error", error=error_str)

            logger.error(
                f"Cache error checking freshness for dataset '{dataset}': {e}"
            )

            # Return not fresh on cache error
            return False, None, message
        except Exception as e:
            # Handle unexpected errors
            error_str = str(e)
            message = self._get_message("error", error=error_str)

            logger.error(
                f"Unexpected error checking freshness for dataset '{dataset}': {e}"
            )

            # Return not fresh on error
            return False, None, message

    def _get_message(self, key: str, **kwargs: int | str) -> str:
        """
        Get localized message with parameter substitution.

        Args:
            key: Message template key (fresh, stale, missing, error)
            **kwargs: Template parameters for substitution

        Returns:
            Formatted message in configured language
        """
        template = self.MESSAGES[key][self.language]
        return template.format(**kwargs)


__all__ = ["FreshnessChecker", "Language"]
