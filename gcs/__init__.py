"""GCS — Ground Control Station software for BDS-SMC2.

Layers (per project plan): portal reader -> decoder -> display -> export (to UAV GCS).
Consumes BeiDou short messages (real portal or sim/virtual_portal) and dispatches a
survivor waypoint.
"""
