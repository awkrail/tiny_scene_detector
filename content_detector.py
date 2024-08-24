from dataclasses import dataclass

import numpy as np
import cv2

from typing import List, NamedTuple, Optional
from enum import Enum

class FlashFilter:
    class Mode(Enum):
        MERGE = 0
        SUPPRESS = 1
    
    def __init__(self, mode: Mode, length: int):
        self._mode = mode
        self._filter_length = length
        self._last_above = None
        self._merge_enabled = False
        self._merge_triggered = False
        self._merge_start = None

    def filter(self, frame_num: int, above_threshold: bool) -> List[int]:
        if not self._filter_length > 0:
            return [frame_num] if above_threshold else []
        if self._last_above is None:
            self._last_above = frame_num
        if self._mode == FlashFilter.Mode.MERGE:
            return self._filter_merge(frame_num=frame_num, above_threshold=above_threshold)
        if self._mode == FlashFilter.Mode.SUPPRESS:
            # SUPRESS mode is not implemented
            raise NotImplementedError
    
    def _filter_merge(self, frame_num: int, above_threshold: bool) -> List[int]:
        min_length_met: bool = (frame_num - self._last_above) >= self._filter_length
        if above_threshold:
            self._last_above = frame_num
        if self._merge_triggered:
            num_merged_frames = self._last_above - self._merge_start
            if min_length_met and not above_threshold and num_merged_frames >= self._filter_length:
                self._merge_triggered = False
                return [self._last_above]
            return []
        
        if not above_threshold:
            return []

        if min_length_met:
            self._merge_enabled = True
            return [frame_num]

        if self._merge_enabled:
            self._merge_enabled = True
            self._merge_start = frame_num
        
        return []

def _mean_pixel_distance(left: np.ndarray, right: np.ndarray) -> float:
    assert len(left.shape) == 2 and len(right.shape) == 2
    assert left.shape == right.shape
    num_pixels: float = float(left.shape[0] * left.shape[1])
    return (np.sum(np.abs(left.astype(np.int32) - right.astype(np.int32))) / num_pixels)

class ContentDetector:

    class Components(NamedTuple):
        delta_hue: float = 1.0
        delta_sat: float = 1.0
        delta_lum: float = 1.0
        delta_edges: float = 0.0
    
    @dataclass
    class _FrameData:
        hue: np.ndarray
        sat: np.ndarray
        lum: np.ndarray
    
    DEFAULT_COMPONENT_WEIGHTS = Components()

    def __init__(
        self,
        threshold: float = 27.0,
        min_scene_len: int = 15,
        weights: 'ContentDetector.Components' = DEFAULT_COMPONENT_WEIGHTS,
        filter_mode: FlashFilter.Mode = FlashFilter.Mode.MERGE,
    ):
        self._threshold: float = threshold
        self._min_scene_len: int = min_scene_len
        self._weights: ContentDetector.Components = weights
        self._last_frame: Optional[ContentDetector._FrameData] = None
        self._flash_filter = FlashFilter(mode=filter_mode, length=min_scene_len)
    
    def process_frame(self, frame_num: int, frame_img: np.ndarray) -> List[int]:
        self._frame_score = self._calculate_frame_score(frame_num, frame_img)
        if self._frame_score is None:
            return []
        
        is_above_threshold = self._frame_score > self._threshold
        return self._flash_filter.filter(frame_num=frame_num, above_threshold=is_above_threshold)
    
    def _calculate_frame_score(self, frame_num: int, frame_img: np.ndarray) -> float:
        hue, sat, lum = cv2.split(cv2.cvtColor(frame_img, cv2.COLOR_BGR2HSV))

        if self._last_frame is None:
            self._last_frame = ContentDetector._FrameData(hue, sat, lum)
            return 0.0
        
        score_components = ContentDetector.Components(
            delta_hue=_mean_pixel_distance(hue, self._last_frame.hue),
            delta_sat=_mean_pixel_distance(sat, self._last_frame.sat),
            delta_lum=_mean_pixel_distance(lum, self._last_frame.lum),
        )

        frame_score: float = (
            sum(component * weight for (component, weight) in zip(score_components, self._weights))
            / sum(abs(weight) for weight in self._weights))

        self._last_frame = ContentDetector._FrameData(hue, sat, lum)
        return frame_score