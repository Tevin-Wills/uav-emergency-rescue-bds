"""
RTK status manager for Level 1 RTK positioning simulation.

Manages simulated RTK fix-state transitions using a time-based model.
This is a software simulation model only — it does not represent real
RTK receiver firmware, satellite signal acquisition, or ambiguity resolution.

Level 1 transition pattern (time-based):
  0–5 seconds:   GNSS_ONLY  (no correction available yet)
  5–15 seconds:  RTK_FLOAT  (correction received, ambiguity not resolved)
  15+ seconds:   RTK_FIXED  (full RTK fix, centimeter-level correction)
"""

# Integer status codes matching the interface contract
STATUS_CODES = {
    'NO_FIX':          0,
    'GNSS_ONLY':       1,
    'RTK_FLOAT':       2,
    'RTK_FIXED':       3,
    'CORRECTION_LOST': 4,
}

STATUS_NAMES = {v: k for k, v in STATUS_CODES.items()}

# Level 1 time thresholds in seconds
_GNSS_ONLY_DURATION_SEC = 5.0
_RTK_FLOAT_DURATION_SEC = 15.0


class RtkStatusManager:
    """
    Controls simulated RTK status transitions for Level 1.

    Usage:
        manager = RtkStatusManager()
        status = manager.update(elapsed_sec=8.0)  # returns 'RTK_FLOAT'
    """

    def __init__(self):
        self._status = 'GNSS_ONLY'

    def update(self, elapsed_sec):
        """
        Update and return the current RTK status based on elapsed simulation time.

        Args:
            elapsed_sec: Seconds since the simulation started.

        Returns:
            Status string: one of GNSS_ONLY, RTK_FLOAT, RTK_FIXED.
        """
        if elapsed_sec < _GNSS_ONLY_DURATION_SEC:
            self._status = 'GNSS_ONLY'
        elif elapsed_sec < _RTK_FLOAT_DURATION_SEC:
            self._status = 'RTK_FLOAT'
        else:
            self._status = 'RTK_FIXED'
        return self._status

    @property
    def status(self):
        """Current status as a string."""
        return self._status

    @property
    def status_code(self):
        """Current status as an integer code (0–4)."""
        return STATUS_CODES.get(self._status, 1)

    def force_status(self, status_name):
        """
        Override status directly (for testing or special conditions like correction loss).

        Args:
            status_name: One of NO_FIX, GNSS_ONLY, RTK_FLOAT, RTK_FIXED, CORRECTION_LOST.
        """
        if status_name in STATUS_CODES:
            self._status = status_name

    @staticmethod
    def code_to_name(code):
        """Convert an integer status code to its string name."""
        return STATUS_NAMES.get(code, 'GNSS_ONLY')

    @staticmethod
    def name_to_code(name):
        """Convert a status string name to its integer code."""
        return STATUS_CODES.get(name, 1)
