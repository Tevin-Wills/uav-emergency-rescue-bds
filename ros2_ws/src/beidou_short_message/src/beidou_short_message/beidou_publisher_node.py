#!/usr/bin/env python3
"""
beidou_publisher_node.py — ROS 2 wrapper around the BeiDou short-message decoder.

Decodes an incoming BeiDou short message (ASCII $CCTXM format) into a rescue
distress coordinate and publishes it on the integration topics:

  /target/emergency_coordinate  (interfaces/EmergencyCoordinate)  -- the rescue trigger
  /rescue/beidou_message        (std_msgs/String)                 -- raw decoded message

The emergency coordinate is published with TRANSIENT_LOCAL (latched) QoS so that
qgc_control / path_planning still receive the distress coordinate even if they
start after this node. It is also re-published on a timer as a heartbeat.

Decode logic mirrors scripts/decode_ascii.py and scripts/decode_binary.py.
Supported message formats:
  ASCII : $CCTXM,<destID>,LAT:<lat>,LON:<lon>*<checksum>
  Binary: $CCTXM,<destID>,BIN:<hex>*<checksum>
          112-bit rescue payload (14 bytes, >iihHBB): lat/lon x1e7, alt m,
          uncertainty R cm, priority, survivor_id — or legacy 64-bit (8 bytes,
          >ii): lat/lon x1e4.
The extra rescue fields (alt/R/priority/survivor_id) are logged but not yet
published — EmergencyCoordinate.msg carries lat/lon only until the interface
extension is agreed with the group.
"""

import math
import struct

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from interfaces.msg import EmergencyCoordinate

# Mean Earth radius (m) for the local equirectangular projection (datum -> lat/lon).
_EARTH_RADIUS_M = 6371000.0


def local_to_latlon(east_m: float, north_m: float, lat0: float, lon0: float):
    """Offset (east, north) metres from a datum -> (lat, lon). Inverse of the
    equirectangular projection used in path_planning/obstacle_map.py."""
    lat0_rad = math.radians(lat0)
    lat = lat0 + math.degrees(north_m / _EARTH_RADIUS_M)
    lon = lon0 + math.degrees(east_m / (_EARTH_RADIUS_M * math.cos(lat0_rad)))
    return lat, lon


def build_cctxm(source_id, lat: float, lon: float) -> str:
    """Format a BeiDou $CCTXM,<id>,LAT:<lat>,LON:<lon>*XX message."""
    return f"$CCTXM,{source_id},LAT:{lat:.4f},LON:{lon:.4f}*XX"


def decode_binary_payload(hex_str: str):
    """Decode a BIN:<hex> payload -> dict with lat/lon (+ rescue fields) or None.

    14 bytes = 112-bit rescue payload: lat,lon (int32 x1e7), alt (int16 m),
    R (uint16 cm), priority (uint8), survivor_id (uint8).
    8 bytes  = legacy coordinate-only payload: lat,lon (int32 x1e4)."""
    try:
        raw = bytes.fromhex(hex_str)
    except ValueError:
        return None
    if len(raw) == 14:
        lat_i, lon_i, alt, r_cm, priority, survivor_id = struct.unpack(">iihHBB", raw)
        return {
            "lat": lat_i / 1e7, "lon": lon_i / 1e7, "alt_m": float(alt),
            "uncertainty_m": r_cm / 100.0, "priority": priority,
            "survivor_id": survivor_id,
        }
    if len(raw) == 8:
        lat_i, lon_i = struct.unpack(">ii", raw)
        return {"lat": lat_i / 1e4, "lon": lon_i / 1e4}
    return None


def decode_message(msg: str):
    """Parse an ASCII or binary $CCTXM message.

    Returns (lat, lon, source_id, extras) where extras is a dict of rescue
    fields (alt_m/uncertainty_m/priority/survivor_id) when present, or
    (None, None, None, None) if the message cannot be decoded."""
    try:
        clean = msg.split("*")[0].strip()
        parts = clean.split(",")
        source_id = parts[1]
        if parts[2].startswith("BIN:"):
            decoded = decode_binary_payload(parts[2][4:])
            if decoded is None:
                return None, None, None, None
            extras = {k: v for k, v in decoded.items() if k not in ("lat", "lon")}
            return decoded["lat"], decoded["lon"], source_id, extras
        lat = float(parts[2].split(":")[1])
        lon = float(parts[3].split(":")[1])
        return lat, lon, source_id, {}
    except (IndexError, ValueError):
        return None, None, None, None


class BeidouPublisherNode(Node):

    def __init__(self):
        super().__init__("beidou_publisher_node")

        # Shared datum (from bringup/config/datum.yaml; defaults = Zurich, matching
        # rtk_positioning's world_origin). The distress coordinate is derived from
        # the datum + an offset, so it auto-stays consistent with the sim home.
        self.declare_parameter("datum_lat", 47.397971057728981)
        self.declare_parameter("datum_lon", 8.5461637398001447)
        self.declare_parameter("target_offset_east_m", 60.0)
        self.declare_parameter("target_offset_north_m", 90.0)
        self.declare_parameter("source_id", "0")
        # raw_message: leave empty to derive from datum+offset; set to override
        # with an explicit $CCTXM message.
        self.declare_parameter("raw_message", "")
        self.declare_parameter("publish_period_sec", 2.0)

        period = float(self.get_parameter("publish_period_sec").value)
        override = str(self.get_parameter("raw_message").value).strip()
        if override:
            self.raw_message = override
        else:
            lat0 = float(self.get_parameter("datum_lat").value)
            lon0 = float(self.get_parameter("datum_lon").value)
            east = float(self.get_parameter("target_offset_east_m").value)
            north = float(self.get_parameter("target_offset_north_m").value)
            src = str(self.get_parameter("source_id").value)
            d_lat, d_lon = local_to_latlon(east, north, lat0, lon0)
            self.raw_message = build_cctxm(src, d_lat, d_lon)
            self.get_logger().info(
                f"Derived distress coordinate from datum ({lat0:.5f},{lon0:.5f}) "
                f"+ offset (E{east:.0f}m,N{north:.0f}m) -> {self.raw_message}")

        # Latched QoS so late subscribers still get the distress coordinate.
        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
        )

        self._pub_coord = self.create_publisher(
            EmergencyCoordinate, "/target/emergency_coordinate", latched)
        self._pub_raw = self.create_publisher(
            String, "/rescue/beidou_message", latched)

        lat, lon, source_id, extras = decode_message(self.raw_message)
        if lat is None:
            self.get_logger().error(
                f"Could not decode BeiDou message: {self.raw_message!r}. Node will idle.")
            self._coord_msg = None
        else:
            self.get_logger().info(
                f"Decoded distress coordinate: lat={lat:.7f}, lon={lon:.7f} (src {source_id})")
            if extras:
                self.get_logger().info(
                    "Rescue payload fields (not yet in EmergencyCoordinate.msg): "
                    f"alt={extras.get('alt_m')}m R={extras.get('uncertainty_m')}m "
                    f"priority=P{extras.get('priority')} "
                    f"survivor_id={extras.get('survivor_id')}")
            self._coord_msg = self._build_coord(lat, lon, source_id)
            self._raw_msg = String(data=self.raw_message)
            self._publish_once()

        # Heartbeat re-publish so the latest coordinate is always observable.
        self._timer = self.create_timer(period, self._publish_once)

    def _build_coord(self, lat, lon, source_id):
        msg = EmergencyCoordinate()
        msg.header.frame_id = "wgs84"
        msg.latitude = lat
        msg.longitude = lon
        msg.source_id = str(source_id)
        msg.raw_message = self.raw_message
        return msg

    def _publish_once(self):
        if self._coord_msg is None:
            return
        now = self.get_clock().now().to_msg()
        self._coord_msg.header.stamp = now
        self._pub_coord.publish(self._coord_msg)
        self._pub_raw.publish(self._raw_msg)


def main(args=None):
    rclpy.init(args=args)
    node = BeidouPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
