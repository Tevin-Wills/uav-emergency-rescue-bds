"""
Coordinate transform for Level 1 RTK positioning simulation.

Converts local ENU (East-North-Up) meter offsets into approximate WGS84
latitude/longitude/altitude using a flat-earth tangent plane approximation.

This is sufficient for Level 1 simulation over short distances (< 1 km).
It does not account for Earth curvature, ellipsoid model, or geodetic datum
corrections — those are unnecessary for a software behavior demonstration.
"""

import math

# Earth radius approximation used for the tangent plane
METERS_PER_DEG_LAT = 111320.0


def enu_to_wgs84(base_lat_deg, base_lon_deg, base_alt_m, east_m, north_m, up_m):
    """
    Convert ENU offsets relative to a base station into WGS84 coordinates.

    Args:
        base_lat_deg: Base station latitude in decimal degrees.
        base_lon_deg: Base station longitude in decimal degrees.
        base_alt_m:   Base station altitude in meters (above ellipsoid).
        east_m:       East offset from base station in meters.
        north_m:      North offset from base station in meters.
        up_m:         Up (vertical) offset from base station in meters.

    Returns:
        (latitude_deg, longitude_deg, altitude_m)
    """
    lat = base_lat_deg + (north_m / METERS_PER_DEG_LAT)
    lon_scale = METERS_PER_DEG_LAT * math.cos(math.radians(base_lat_deg))
    lon = base_lon_deg + (east_m / lon_scale)
    alt = base_alt_m + up_m
    return lat, lon, alt


def wgs84_to_enu(base_lat_deg, base_lon_deg, base_alt_m, lat_deg, lon_deg, alt_m):
    """
    Convert WGS84 coordinates back into ENU offsets relative to a base station.

    Args:
        base_lat_deg: Base station latitude in decimal degrees.
        base_lon_deg: Base station longitude in decimal degrees.
        base_alt_m:   Base station altitude in meters.
        lat_deg:      Target latitude in decimal degrees.
        lon_deg:      Target longitude in decimal degrees.
        alt_m:        Target altitude in meters.

    Returns:
        (east_m, north_m, up_m)
    """
    north_m = (lat_deg - base_lat_deg) * METERS_PER_DEG_LAT
    lon_scale = METERS_PER_DEG_LAT * math.cos(math.radians(base_lat_deg))
    east_m = (lon_deg - base_lon_deg) * lon_scale
    up_m = alt_m - base_alt_m
    return east_m, north_m, up_m
