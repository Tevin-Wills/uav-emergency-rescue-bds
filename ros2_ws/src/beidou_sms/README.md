# beidou_sms

**Owner:** Member 5  
**Responsibility:** BeiDou short message send/receive and rescue coordinate forwarding.

## Overview

This package interfaces with the BeiDou short message communication hardware or simulator. It decodes incoming short messages to extract rescue coordinates and forwards them to the rest of the system via ROS2.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/beidou/rescue_coords` | TBD | Decoded rescue coordinates from incoming SMS |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/beidou/send_message` | TBD | Outgoing message requests |

## Package Structure

```
beidou_sms/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## TODO

- [ ] Implement BeiDou hardware serial interface or simulator
- [ ] Implement message decode logic
- [ ] Publish rescue coordinates to ROS2
- [ ] Document BeiDou message format in `config/` and `docs/`
