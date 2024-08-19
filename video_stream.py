import os
import cv2
import math

from typing import Optional, Tuple
from frame_timecode import FrameTimecode, MAX_FPS_DELTA

class VideoStreamCv2:
    """
    OpenCV cv2.VideoCapture backend
    """
    def __init__(
            self,
            path: str,
            framerate: Optional[float] = None,
    ):
        if path is None:
            raise ValueError('Path must be specified')
        self._path = path
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_rate: Optional[float] = framerate
        self._num_frames = 0
        self._open_capture(framerate)

    @property
    def frame_number(self) -> int:
        return self._num_frames
    
    @property
    def frame_rate(self) -> float:
        return self._cap.framerate
    
    @property
    def frame_size(self) -> Tuple[int, int]:
        return (math.trunc(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                math.trunc(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    @property
    def base_timecode(self) -> FrameTimecode:
        return FrameTimecode(timecode=0, fps=self._frame_rate)

    @property
    def position(self) -> FrameTimecode:
        if self.frame_number < 1:
            return self.base_timecode
        return self.base_timecode + (self.frame_number - 1)

    @property
    def duration(self) -> Optional[FrameTimecode]:
        return self.base_timecode + math.trunc(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def _open_capture(
            self,
            framerate: Optional[float] = None,
    ):
        if not os.path.exists(self._path):
            raise OSError('Video file not found.')

        cap = cv2.VideoCapture(self._path)        
        if not cap.isOpened():
            raise OSError('Ensure file is valid video.')

        codec_unsupported: bool = int(abs(cap.get(cv2.CAP_PROP_FOURCC))) == 0
        if codec_unsupported:
            raise Exception("Video codec detection failed. Unsupported video codec.")

        assert framerate is None or framerate > MAX_FPS_DELTA, "Framerate must be validated if set."
        if framerate is None:
            framerate = cap.get(cv2.CAP_PROP_FPS)
            if framerate < MAX_FPS_DELTA:
                raise Exception("Frame rate is unavailable.")
            
        self._cap = cap
        self._frame_rate = framerate