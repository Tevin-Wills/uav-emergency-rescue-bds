# Student 5 — BeiDou Short Message Report

## Assigned Objective

BeiDou Short Message Communication — interface with the BeiDou short message service to receive emergency rescue coordinates and forward them to the UAV system via ROS 2.

## Personal Report Scope

- Background on BeiDou satellite navigation system and its short message capability.
- Short message protocol design and coordinate encoding/decoding.
- ROS 2 node design for `beidou_short_message`.
- Simulation of BeiDou message reception using software.
- Simulation setup and test results.

## Expected Simulation Evidence

- Decoded BeiDou message log showing correct coordinate extraction.
- ROS 2 topic echo for `/rescue/beidou_message` and `/target/emergency_coordinate`.
- Sample message file in `data/sample_beidou_message.json`.

## Folder Structure

```
student_5_beidou_short_message/
├── README.md
├── outline.md
├── figures/
├── tables/
└── references/
```
