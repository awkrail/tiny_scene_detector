import queue
import threading
import cv2
import numpy as np

from typing import Tuple, Optional, Callable

from content_detector import ContentDetector
from video_stream import VideoStreamCv2
from frame_timecode import FrameTimecode

DEFAULT_MIN_WIDTH: int = 256
MAX_FRAME_QUEUE_LENGTH: int = 4

def compute_downscale_factor(frame_width: int, effective_width: int = DEFAULT_MIN_WIDTH) -> int:
    if frame_width < effective_width:
        return 1
    return frame_width // effective_width


class SceneManager:
    def __init__(
        self,
        detector: ContentDetector
    ):
        self._detector: ContentDetector = detector
        self._frame_size: Tuple[int, int] = None
        self._start_pos: FrameTimecode = None
        self._last_pos: FrameTimecode = None
        self._base_timecode: Optional[FrameTimecode] = None
        self._stop = threading.Event()
        self._frame_buffer = []
        self._frame_buffer_size = 0
        self._cutting_list = []

    def detect_scenes(
        self,
        video: VideoStreamCv2,
    ):
        if video is None:
            raise TypeError("detect_scenes() missing 1 required positional argument: 'video'")
        
        self._base_timecode = video.base_timecode
        total_frames = video.duration.frame_num
        downscale_factor = compute_downscale_factor(video.frame_size[0])

        frame_queue = queue.Queue(MAX_FRAME_QUEUE_LENGTH)
        self._stop.clear()
        decoder_thread = threading.Thread(
            target=SceneManager._decode_thread,
            args=(self, video, downscale_factor, frame_queue)
        )
        decoder_thread.start()
        frame_im = None        

        while not self._stop.is_set():
            next_frame, position = frame_queue.get()
            if next_frame is None and position is None:
                break
            if not next_frame is None:
                frame_im = next_frame
            
            new_cuts = self._process_frame(position.frame_num, frame_im)

        while not frame_queue.empty():
            frame_queue.get_nowait()
        decoder_thread.join()

        self._last_pos = video.position
        self._post_process(video.position.frame_num)
        return video.frame_number

    def _process_frame(
        self,
        frame_num: int,
        frame_im: np.ndarray,
    ) -> bool:
        new_cuts = False
        self._frame_buffer.append(frame_im)
        self._frame_buffer = self._frame_buffer[-(self._frame_buffer_size + 1):]
        cuts = self._detector.process_frame(frame_num, frame_im)
        self._cutting_list += cuts
        new_cuts = True if cuts else False
        return new_cuts

    def _decode_thread(
        self,
        video: VideoStreamCv2,
        downscale_factor: int,
        out_queue: queue.Queue
    ):
        while not self._stop.is_set():
            frame_im = video.read()

            if frame_im is False:
                break

            decoded_size = (frame_im.shape[1], frame_im.shape[0])
            if self._frame_size is None:
                self._frame_size = decoded_size
            
            if downscale_factor > 1:
                frame_im = cv2.resize(
                    frame_im, (round(frame_im.shape[1] / downscale_factor),
                                round(frame_im.shape[0] / downscale_factor)),
                    interpolation=cv2.INTER_LINEAR
                )
            
            if self._start_pos is None:
                self._start_pos = video.position
            
            out_queue.put((frame_im, video.position))
        
        out_queue.put((None, None))