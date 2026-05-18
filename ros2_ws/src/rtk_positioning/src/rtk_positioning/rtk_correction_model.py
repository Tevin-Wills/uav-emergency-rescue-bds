"""
RTK correction model for Level 1 RTK positioning simulation.

Models the effect of RTK correction by selecting the noise level that
corresponds to the current RTK status. This is not real RTCM processing —
no correction bytes are decoded and no carrier-phase ambiguity is resolved.
"""

from rtk_positioning.gnss_noise_model import GnssNoiseModel


class RtkCorrectionModel:
    """
    Applies simulated RTK correction behavior by noise reduction.

    The 'correction' is modelled as a reduction in position noise:
      - GNSS_ONLY: standard GNSS noise (~1.5 m)
      - RTK_FLOAT: reduced noise (~0.25 m)
      - RTK_FIXED: minimal noise (~0.03 m)
      - CORRECTION_LOST: degraded noise (~2.5 m)
    """

    def __init__(self, noise_model: GnssNoiseModel):
        self._noise = noise_model

    def apply_correction(self, position_m, rtk_status):
        """
        Return a corrected position by applying the noise level for the given status.

        Args:
            position_m: numpy array [x, y, z] representing true position in meters.
            rtk_status: string — one of GNSS_ONLY, RTK_FLOAT, RTK_FIXED, CORRECTION_LOST.

        Returns:
            numpy array [x, y, z] with status-appropriate noise applied.
        """
        return self._noise.apply_noise(position_m, mode=rtk_status)

    def apply_raw_gnss(self, position_m):
        """
        Return a raw GNSS position (always uses GNSS_ONLY noise level).

        Args:
            position_m: numpy array [x, y, z] representing true position in meters.

        Returns:
            numpy array [x, y, z] with GNSS_ONLY noise applied.
        """
        return self._noise.apply_noise(position_m, mode='GNSS_ONLY')

    def get_accuracy_m(self, rtk_status):
        """Return the expected horizontal accuracy in meters for a given status."""
        return self._noise.get_std(mode=rtk_status)
