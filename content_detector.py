from dataclasses import dataclass

import numpy as np
import cv2

from typing import List, NamedTuple, Optional
from enum import Enum

class FlashFilter:
    class Mode(Enum):
        MERGE = 0
        SUPPRESS = 1

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
        # self._flash_filter = FlashFilter(mode=filter_mode, length=min_scene_len)
    
    def process_frame(self, frame_num: int, frame_img: np.ndarray) -> List[int]:
        self._frame_score = self._calculate_frame_score(frame_num, frame_img)
        if self._frame_score is None:
            return []
        
        is_above_threshold = self._frame_score > self._threshold
        return self._flash_filter.filter(frame_num=frame_num, above_treshold=is_above_threshold)
    
    def _calculate_frame_score(self, frame_num: int, frame_img: np.ndarray) -> float:
        import ipdb; ipdb.set_trace()
        hue, sat, lum = cv2.split(cv2.cvtColor(frame_img, cv2.COLOR_BGR2HSV))

        if self._last_frame is None:
            self._last_frame = ContentDetector._FrameData(hue, sat, lum)
            return 0.0
        
        score_components = ContentDetector.Components(
            delta_hue=_mean_pixel_distance(hue, self._last_frame.hue),
            delta_sat=_mean_pixel_distance(sat, self._last_frame.sat),
            delta_lum=_mean_pixel_distance(lum, self._last_frame.lum),
        )