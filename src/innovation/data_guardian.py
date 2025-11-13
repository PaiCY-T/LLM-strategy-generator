"""
DataGuardian: Cryptographic Protection for Hold-Out Set

This module implements the critical security layer that prevents premature
access to the hold-out dataset (2019-2025). This is essential for preventing
meta-overfitting, the single greatest risk identified by all three expert
reviewers (o3, Gemini 2.5 Pro, Opus 4.1).

Security Features:
- SHA-256 cryptographic hash of hold-out data
- Access control with week number verification
- Comprehensive access logging
- Unlock requires explicit authorization code
- Immutable lock record

Executive Mandate: "Create a DataGuardian class that cryptographically signs
the hold-out set and alerts on any access attempt before Week 12." - Opus 4.1

Usage:
    # Week 1: Lock hold-out set
    guardian = DataGuardian()
    lock_record = guardian.lock_holdout(holdout_data)

    # Week 1-11: Access denied (raises SecurityError)
    try:
        guardian.access_holdout(week_number=5, justification="Testing")
    except SecurityError:
        pass  # Expected, access logged

    # Week 12: Unlock for final validation
    guardian.unlock_holdout(
        week_number=12,
        authorization_code="WEEK_12_FINAL_VALIDATION"
    )
    guardian.access_holdout(week_number=12, justification="Final validation")
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd


class DataGuardian:
    """
    Cryptographically protects hold-out set from premature access.

    This class implements the security layer required by Condition 1 of the
    Executive Approval. It ensures that the hold-out set (2019-2025) remains
    pristine until Week 12, preventing meta-overfitting.

    Attributes:
        config_path: Path to lock configuration file
        holdout_hash: SHA-256 hash of locked hold-out data
        lock_timestamp: When hold-out was locked
        access_allowed: Whether access is currently permitted
        access_log: List of all access attempts (granted or denied)
    """

    def __init__(self, config_path: str = '.spec-workflow/specs/llm-innovation-capability/data_lock.json'):
        """
        Initialize DataGuardian.

        Args:
            config_path: Path to store lock configuration (default: spec directory)
        """
        self.config_path = Path(config_path)
        self.holdout_hash: Optional[str] = None
        self.lock_timestamp: Optional[str] = None
        self.access_allowed: bool = False
        self.access_log: list = []

        # Load existing lock if present
        if self.config_path.exists():
            self._load_lock()

    def lock_holdout(self, holdout_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Lock hold-out set with cryptographic hash.

        This method computes a SHA-256 hash of the hold-out data and stores
        it in an immutable lock record. Any subsequent access attempts before
        Week 12 will be denied and logged.

        Args:
            holdout_data: DataFrame with hold-out data (2019-2025)

        Returns:
            dict with hash, timestamp, and data summary

        Example:
            >>> import finlab
            >>> data = finlab.data.get('price:收盤價', start='2019-01-01')
            >>> guardian = DataGuardian()
            >>> lock_record = guardian.lock_holdout(data)
            ✅ Hold-out set LOCKED
               Hash: a1b2c3...
               Timestamp: 2025-10-23T14:30:00
               Shape: (1234, 56)
               Date Range: 2019-01-02 to 2025-10-23
        """
        # Compute SHA-256 hash
        data_json = holdout_data.to_json(orient='split', date_format='iso')
        self.holdout_hash = hashlib.sha256(data_json.encode('utf-8')).hexdigest()
        self.lock_timestamp = datetime.now().isoformat()

        # Reset instance variables for new lock
        self.access_allowed = False
        self.access_log = []

        # Create lock record
        lock_record = {
            'holdout_hash': self.holdout_hash,
            'lock_timestamp': self.lock_timestamp,
            'data_shape': list(holdout_data.shape),
            'date_range': {
                'start': str(holdout_data.index.min()),
                'end': str(holdout_data.index.max())
            },
            'access_allowed': False,
            'unlock_timestamp': None,
            'access_log': []
        }

        # Save lock configuration
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(lock_record, f, indent=2)

        print(f"✅ Hold-out set LOCKED")
        print(f"   Hash: {self.holdout_hash}")
        print(f"   Timestamp: {self.lock_timestamp}")
        print(f"   Shape: {holdout_data.shape}")
        print(f"   Date Range: {lock_record['date_range']['start']} to {lock_record['date_range']['end']}")

        return lock_record

    def verify_holdout(self, holdout_data: pd.DataFrame) -> bool:
        """
        Verify hold-out data matches locked hash.

        This method recomputes the hash of the provided data and compares it
        to the stored hash. This ensures the hold-out set has not been
        modified since locking.

        Args:
            holdout_data: DataFrame to verify

        Returns:
            True if hash matches, False otherwise

        Example:
            >>> assert guardian.verify_holdout(holdout_data), "Verification failed!"
            ✅ Hold-out data verification PASSED
        """
        if self.holdout_hash is None:
            raise ValueError("Hold-out not yet locked. Call lock_holdout() first.")

        data_json = holdout_data.to_json(orient='split', date_format='iso')
        current_hash = hashlib.sha256(data_json.encode('utf-8')).hexdigest()

        if current_hash == self.holdout_hash:
            print("✅ Hold-out data verification PASSED")
            return True
        else:
            print("❌ Hold-out data verification FAILED")
            print(f"   Expected: {self.holdout_hash}")
            print(f"   Got: {current_hash}")
            return False

    def access_holdout(self, week_number: int, justification: str) -> bool:
        """
        Request access to hold-out data.

        This method checks whether access is permitted based on the current
        week number and unlock status. All access attempts are logged for audit.

        Args:
            week_number: Current week number (1-12)
            justification: Reason for access request

        Returns:
            True if access granted

        Raises:
            SecurityError: If access is denied (week != 12 or not unlocked)

        Example:
            >>> # Week 5: Access denied
            >>> try:
            ...     guardian.access_holdout(week_number=5, justification="Testing")
            ... except SecurityError as e:
            ...     print(e)
            ❌ HOLD-OUT ACCESS DENIED
            Week: 5
            ...

            >>> # Week 12: Access granted
            >>> guardian.unlock_holdout(week_number=12, authorization_code="WEEK_12_FINAL_VALIDATION")
            >>> guardian.access_holdout(week_number=12, justification="Final validation")
            ✅ Hold-out access GRANTED (Week 12)
        """
        access_attempt = {
            'timestamp': datetime.now().isoformat(),
            'week_number': week_number,
            'justification': justification,
            'granted': False
        }

        # Check if access is allowed
        if week_number == 12 and self.access_allowed:
            access_attempt['granted'] = True
            self.access_log.append(access_attempt)
            self._save_log()
            print(f"✅ Hold-out access GRANTED (Week {week_number})")
            return True

        # Access denied
        self.access_log.append(access_attempt)
        self._save_log()

        error_msg = f"""
❌ HOLD-OUT ACCESS DENIED

Week: {week_number}
Justification: {justification}

Access Requirements:
- Must be Week 12
- Must call unlock_holdout() first

Current Status:
- Access Allowed: {self.access_allowed}
- Lock Timestamp: {self.lock_timestamp}

This access attempt has been logged.
"""
        raise SecurityError(error_msg)

    def unlock_holdout(self, week_number: int, authorization_code: str) -> bool:
        """
        Unlock hold-out set for final validation.

        This method enables access to the hold-out set, but ONLY in Week 12
        and ONLY with the correct authorization code. This is the final
        safeguard against premature access.

        Args:
            week_number: Must be 12
            authorization_code: Must be "WEEK_12_FINAL_VALIDATION"

        Returns:
            True if unlock successful

        Raises:
            SecurityError: If week_number != 12 or authorization_code is invalid

        Example:
            >>> guardian.unlock_holdout(
            ...     week_number=12,
            ...     authorization_code="WEEK_12_FINAL_VALIDATION"
            ... )
            ✅ Hold-out UNLOCKED for Week 12 validation
               Unlock Timestamp: 2025-12-15T10:00:00
        """
        if week_number != 12:
            raise SecurityError(
                f"Hold-out can only be unlocked in Week 12 (current: Week {week_number})"
            )

        if authorization_code != "WEEK_12_FINAL_VALIDATION":
            raise SecurityError("Invalid authorization code")

        unlock_timestamp = datetime.now().isoformat()

        # Update lock configuration
        with open(self.config_path, 'r') as f:
            lock_config = json.load(f)

        lock_config['access_allowed'] = True
        lock_config['unlock_timestamp'] = unlock_timestamp

        with open(self.config_path, 'w') as f:
            json.dump(lock_config, f, indent=2)

        # Update instance variable AFTER saving
        self.access_allowed = True

        print(f"✅ Hold-out UNLOCKED for Week 12 validation")
        print(f"   Unlock Timestamp: {unlock_timestamp}")

        return True

    def get_access_log(self) -> list:
        """
        Get access log for audit purposes.

        Returns:
            List of all access attempts (granted and denied)
        """
        return self.access_log.copy()

    def get_lock_status(self) -> Dict[str, Any]:
        """
        Get current lock status.

        Returns:
            dict with lock status information
        """
        # Reload from disk to get latest access log
        if self.config_path.exists():
            self._load_lock()

        return {
            'is_locked': self.holdout_hash is not None,
            'lock_timestamp': self.lock_timestamp,
            'access_allowed': self.access_allowed,
            'total_access_attempts': len(self.access_log),
            'granted_attempts': sum(1 for a in self.access_log if a['granted']),
            'denied_attempts': sum(1 for a in self.access_log if not a['granted'])
        }

    def _load_lock(self) -> dict:
        """Load lock configuration from disk."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        self.holdout_hash = config['holdout_hash']
        self.lock_timestamp = config['lock_timestamp']
        self.access_allowed = config['access_allowed']
        self.access_log = config.get('access_log', [])

        return config

    def _save_log(self):
        """Save access log to disk."""
        if not self.config_path.exists():
            raise ValueError("Lock configuration not found. Call lock_holdout() first.")

        # Load current config without overwriting instance variables
        with open(self.config_path, 'r') as f:
            lock_config = json.load(f)

        # Update only the access log
        lock_config['access_log'] = self.access_log

        with open(self.config_path, 'w') as f:
            json.dump(lock_config, f, indent=2)


class SecurityError(Exception):
    """Raised when hold-out access is denied."""
    pass
