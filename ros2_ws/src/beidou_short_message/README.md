# beidou_short_message

**Owner:** Student 5
**Responsibility:** BeiDou short message receive, decode, and rescue coordinate forwarding.

## Overview

This package interfaces with the BeiDou short message communication hardware or software simulator. It decodes incoming short messages to extract rescue coordinates and forwards them to the rest of the system via ROS 2.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/rescue/beidou_message` | Custom | Raw decoded BeiDou short message |
| `/target/emergency_coordinate` | Custom | Extracted rescue coordinate from message |

## Subscribed Topics

None (input comes from BeiDou hardware/simulator interface, not a ROS 2 topic).

## Package Structure

```
beidou_short_message/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## Integration

- `qgc_control` subscribes to `/target/emergency_coordinate` to plan and upload the mission.
- `path_planning` subscribes to `/target/emergency_coordinate` to compute the route.

See [`interfaces/integration_contract.md`](../../../../interfaces/integration_contract.md) for the full contract.

## TODO

- [ ] Implement BeiDou hardware serial interface or software simulator
- [ ] Implement message decode logic
- [ ] Publish decoded coordinate to `/target/emergency_coordinate`
- [ ] Document BeiDou message format in `docs/`
