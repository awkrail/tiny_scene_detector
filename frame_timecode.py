import math
from typing import Union

MAX_FPS_DELTA: float = 1.0 / 100000

class FrameTimecode:
    def __init__(
        self,
        timecode: Union[int, float, str, 'FrameTimecode'] = None,
        fps: Union[int, float, str, 'FrameTimecode'] = None
        ):
        self._framerate = None
        self._frame_num = None

        if isinstance(timecode, FrameTimecode):
            self._framerate = timecode.framerate
            self.frame_num = timecode.frame_num
            if fps is not None:
                pass
    
    @property
    def framerate(self):
        return self._framerate
    
    @property
    def frame_num(self):
        return self._frame_num