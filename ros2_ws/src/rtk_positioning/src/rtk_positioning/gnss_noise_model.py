"""
GNSS noise model for Level 1 RTK positioning simulation.

Applies Gaussian noise in meters to simulate positioning error at different
correction quality levels. This is a software behavior model only — it does
not simulate real satellite signals, ionospheric effects, or multipath.
"""

import numpy as np

# Noise standard deviations in meters, matching config/noise_profiles.yaml
NOISE_STD_M = {
    'GNSS_ONLY':       1.5,
    'RTK_FLOAT':       0.25,
    'RTK_FIXED':       0.03,
    'CORRECTION_LOST': 2.5,
}


class GnssNoiseModel:
    """Applies Gaussian position noise based on the current GNSS/RTK mode."""

    def __init__(self, seed=None):
        """
        Args:
            seed: Optional integer seed for reproducible noise sequences.
        """
        self._rng = np.random.default_rng(seed)

    def apply_noise(self, position_m, mode='GNSS_ONLY'):
        """
        Add Gaussian noise to a 3D position vector.

        Args:
            position_m: numpy array [x, y, z] in meters (ENU).
            mode: one of GNSS_ONLY, RTK_FLOAT, RTK_FIXED, CORRECTION_LOST.

        Returns:
            numpy array [x, y, z] with noise applied.
        """
        std = NOISE_STD_M.get(mode, NOISE_STD_M['GNSS_ONLY'])
        noise = self._rng.normal(0.0, std, size=3)
        return position_m + noise

    def get_std(self, mode='GNSS_ONLY'):
        """Return the noise standard deviation in meters for a given mode."""
        return NOISE_STD_M.get(mode, NOISE_STD_M['GNSS_ONLY'])

    def update_from_config(self, config):
        """
        Override noise values from a loaded YAML config dict.

        Args:
            config: dict with keys matching NOISE_STD_M (e.g. 'normal_gnss_std_m').
        """
        if 'normal_gnss_std_m' in config:
            NOISE_STD_M['GNSS_ONLY'] = config['normal_gnss_std_m']
        if 'rtk_float_std_m' in config:
            NOISE_STD_M['RTK_FLOAT'] = config['rtk_float_std_m']
        if 'rtk_fixed_std_m' in config:
            NOISE_STD_M['RTK_FIXED'] = config['rtk_fixed_std_m']
        if 'correction_lost_std_m' in config:
            NOISE_STD_M['CORRECTION_LOST'] = config['correction_lost_std_m']
