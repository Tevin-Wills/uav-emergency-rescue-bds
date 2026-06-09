"""Stable target track assignment without ROS dependencies."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class TrackState:
    bbox_xyxy: list[float]
    position_m: tuple[float, float, float] | None
    velocity_m_per_frame: tuple[float, float, float] | None
    image_track_id: int | None
    missing: int
    last_frame_index: int


def bbox_iou(box_a: list[float], box_b: list[float]) -> float:
    ax0, ay0, ax1, ay1 = box_a
    bx0, by0, bx1, by1 = box_b
    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)
    iw = max(0.0, ix1 - ix0)
    ih = max(0.0, iy1 - iy0)
    intersection = iw * ih
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - intersection
    return intersection / union if union > 0.0 else 0.0


def distance_3d(
    point_a: tuple[float, float, float] | None,
    point_b: tuple[float, float, float] | None,
) -> float | None:
    if point_a is None or point_b is None:
        return None
    return math.sqrt(sum((point_a[index] - point_b[index]) ** 2 for index in range(3)))


def predict_position(state: TrackState, frame_index: int) -> tuple[float, float, float] | None:
    if state.position_m is None:
        return None
    if state.velocity_m_per_frame is None:
        return state.position_m
    dt = max(1, frame_index - state.last_frame_index)
    return tuple(
        state.position_m[index] + state.velocity_m_per_frame[index] * dt
        for index in range(3)
    )


class HybridTrackManager:
    """Assign stable rescue IDs using image ID, bbox IoU, and 3D position."""

    def __init__(
        self,
        iou_threshold: float = 0.25,
        max_missing: int = 12,
        position_distance_threshold_m: float = 4.0,
        min_score: float = 0.35,
        image_track_weight: float = 0.45,
        iou_weight: float = 0.25,
        position_weight: float = 0.55,
        smoothing: float = 0.35,
    ):
        self.iou_threshold = float(iou_threshold)
        self.max_missing = int(max_missing)
        self.position_distance_threshold_m = float(position_distance_threshold_m)
        self.min_score = float(min_score)
        self.image_track_weight = float(image_track_weight)
        self.iou_weight = float(iou_weight)
        self.position_weight = float(position_weight)
        self.smoothing = float(smoothing)
        self.next_id = 1
        self.frame_index = 0
        self.tracks: dict[int, TrackState] = {}
        self.image_to_stable: dict[int, int] = {}

    def _new_track_id(self) -> int:
        track_id = self.next_id
        self.next_id += 1
        return track_id

    def _score(self, target, position_m, state: TrackState) -> tuple[float, str]:
        score = 0.0
        reasons: list[str] = []

        if target.image_track_id is not None and target.image_track_id == state.image_track_id:
            score += self.image_track_weight
            reasons.append("image_tracker")

        iou = bbox_iou(target.bbox_xyxy, state.bbox_xyxy)
        if iou >= self.iou_threshold:
            score += self.iou_weight * min(1.0, iou / max(self.iou_threshold, 1e-6))
            reasons.append("bbox_iou")

        predicted = predict_position(state, self.frame_index)
        distance = distance_3d(position_m, predicted)
        if distance is not None and distance <= self.position_distance_threshold_m:
            closeness = 1.0 - distance / self.position_distance_threshold_m
            score += self.position_weight * closeness
            reasons.append("position")

        return (score, "+".join(reasons)) if reasons else (0.0, "new")

    def _update_state(self, track_id: int, target, position_m) -> None:
        previous = self.tracks.get(track_id)
        velocity = None
        smoothed_position = position_m

        if previous and previous.position_m is not None and position_m is not None:
            dt = max(1, self.frame_index - previous.last_frame_index)
            measured_velocity = tuple(
                (position_m[index] - previous.position_m[index]) / dt
                for index in range(3)
            )
            if previous.velocity_m_per_frame is None:
                velocity = measured_velocity
            else:
                velocity = tuple(
                    (1.0 - self.smoothing) * previous.velocity_m_per_frame[index]
                    + self.smoothing * measured_velocity[index]
                    for index in range(3)
                )
            predicted = predict_position(previous, self.frame_index)
            if predicted is not None:
                smoothed_position = tuple(
                    (1.0 - self.smoothing) * predicted[index]
                    + self.smoothing * position_m[index]
                    for index in range(3)
                )
        elif previous:
            velocity = previous.velocity_m_per_frame
            smoothed_position = position_m if position_m is not None else previous.position_m

        self.tracks[track_id] = TrackState(
            bbox_xyxy=target.bbox_xyxy,
            position_m=smoothed_position,
            velocity_m_per_frame=velocity,
            image_track_id=target.image_track_id,
            missing=0,
            last_frame_index=self.frame_index,
        )
        if target.image_track_id is not None:
            self.image_to_stable[target.image_track_id] = track_id

    def update(self, targets, positions_m: list[tuple[float, float, float] | None]) -> None:
        unmatched_track_ids = set(self.tracks)
        assignments: list[tuple[float, int, int, str]] = []

        for target_index, target in enumerate(targets):
            mapped_id = (
                self.image_to_stable.get(target.image_track_id)
                if target.image_track_id is not None
                else None
            )
            if mapped_id in unmatched_track_ids:
                assignments.append((999.0, target_index, mapped_id, "image_tracker"))
                continue

            for track_id in unmatched_track_ids:
                score, source = self._score(
                    target,
                    positions_m[target_index],
                    self.tracks[track_id],
                )
                if score >= self.min_score:
                    assignments.append((score, target_index, track_id, source))

        assigned_targets: set[int] = set()
        assigned_tracks: set[int] = set()
        for _score, target_index, track_id, source in sorted(assignments, reverse=True):
            if target_index in assigned_targets or track_id in assigned_tracks:
                continue
            target = targets[target_index]
            target.track_id = track_id
            target.track_source = source
            self._update_state(track_id, target, positions_m[target_index])
            assigned_targets.add(target_index)
            assigned_tracks.add(track_id)

        for target_index, target in enumerate(targets):
            if target_index in assigned_targets:
                continue
            track_id = self._new_track_id()
            target.track_id = track_id
            target.track_source = "new"
            self._update_state(track_id, target, positions_m[target_index])
            assigned_tracks.add(track_id)

        for track_id in list(unmatched_track_ids - assigned_tracks):
            state = self.tracks[track_id]
            state.missing += 1
            if state.missing > self.max_missing:
                if state.image_track_id is not None:
                    self.image_to_stable.pop(state.image_track_id, None)
                del self.tracks[track_id]

        self.frame_index += 1
