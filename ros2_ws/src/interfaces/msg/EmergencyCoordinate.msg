# Rescue distress coordinate extracted from a decoded BeiDou short message.
# Published by beidou_short_message on /target/emergency_coordinate to trigger
# mission planning. Consumed by qgc_control and path_planning.
std_msgs/Header header

float64 latitude        # decimal degrees (WGS-84)
float64 longitude       # decimal degrees (WGS-84)
string source_id        # BeiDou terminal / destination ID that sent the message
string raw_message       # original decoded short message (e.g. "$CCTXM,0,LAT:..,LON:..")
