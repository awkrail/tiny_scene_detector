import os
import cv2

from typing import Optional
from frame_timecode import MAX_FPS_DELTA

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
        self._open_capture(framerate)

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