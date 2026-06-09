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

Decode logic mirrors scripts/decode_ascii.py (message format:
$CCTXM,<destID>,LAT:<lat>,LON:<lon>*<checksum>).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from interfaces.msg import EmergencyCoordinate

# Default sample distress message (Yuhang District, Hangzhou — same as decode scripts).
DEFAULT_MESSAGE = "$CCTXM,0,LAT:30.4196,LON:120.2977*XX"


def decode_ascii(msg: str):
    """Parse $CCTXM,<destID>,LAT:<lat>,LON:<lon>*CS -> (lat, lon, source_id) or (None, None, None)."""
    try:
        clean = msg.split("*")[0].strip()
        parts = clean.split(",")
        source_id = parts[1]
        lat = float(parts[2].split(":")[1])
        lon = float(parts[3].split(":")[1])
        return lat, lon, source_id
    except (IndexError, ValueError):
        return None, None, None


class BeidouPublisherNode(Node):

    def __init__(self):
        super().__init__("beidou_publisher_node")

        self.declare_parameter("raw_message", DEFAULT_MESSAGE)
        self.declare_parameter("publish_period_sec", 2.0)

        self.raw_message = self.get_parameter("raw_message").value
        period = float(self.get_parameter("publish_period_sec").value)

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

        lat, lon, source_id = decode_ascii(self.raw_message)
        if lat is None:
            self.get_logger().error(
                f"Could not decode BeiDou message: {self.raw_message!r}. Node will idle.")
            self._coord_msg = None
        else:
            self.get_logger().info(
                f"Decoded distress coordinate: lat={lat:.4f}, lon={lon:.4f} (src {source_id})")
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
