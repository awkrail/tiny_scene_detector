import math
from typing import Union

MAX_FPS_DELTA: float = 1.0 / 100000

_SECONDS_PER_MINUTE = 60.0
_SECONDS_PER_HOUR = 60.0 * _SECONDS_PER_MINUTE
_MINUTES_PER_HOUR = 60.0

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
                raise TypeError('Framerate cannot be overwritten when copying a FrameTimecode.')
        else:
            if isinstance(fps, FrameTimecode):
                fps  = fps.framerate
            
            if not isinstance(fps, (int, float)):
                raise TypeError('Framerate must be of type int/float.')

            if (isinstance(fps, int) and not fps > 0) or (isinstance(fps, float) 
                                                          and not fps >= MAX_FPS_DELTA):
                raise ValueError('Framerate must be positive and greater than zero.')
            self._framerate = float(fps)

        if isinstance(timecode, str):
            self._frame_num = self._parse_timecode_string(timecode)
        else:
            self._frame_num = self._parse_timecode_number(timecode)
    
    @property
    def framerate(self) -> float:
        return self._framerate
    
    @property
    def frame_num(self) -> int:
        return self._frame_num
    
    @property
    def seconds(self) -> float:
        return float(self.frame_num) / self.framerate

    @property
    def timecode(self, precision: int = 3, use_rounding: bool = True) -> str:
        """
        Get a formatted timecode string: HH:MM:SS[.nnn].
        """
        secs = self.seconds
        hrs = int(secs / _SECONDS_PER_HOUR)
        secs -= (hrs * _SECONDS_PER_HOUR)
        mins = int(secs / _SECONDS_PER_MINUTE)
        secs = max(0.0, secs - (mins * _SECONDS_PER_MINUTE))
        if use_rounding:
            secs = round(secs, precision)
        secs = min(_SECONDS_PER_MINUTE, secs)
        if int(secs) == _SECONDS_PER_MINUTE:
            secs = 0.0
            mins += 1
            if mins >= _MINUTES_PER_HOUR:
                mins = 0
                hrs += 1
        
        msec = format(secs, '.%df' % (precision + 1)) if precision else ''
        msec_str = msec[-(2 + precision):-1]
        secs_str = f"{int(secs):02d}{msec_str}"
        return '{:02d}:{:02d}:{}'.format(hrs, mins, secs_str)

    def equal_framerate(self, fps: float) -> bool:
        return math.fabs(self.framerate - fps) < MAX_FPS_DELTA

    def _parse_timecode_string(self, input: str) -> int:
        """
        Parse a string into the exact number of frames.
        Valid timestamps
          - 00:05:00.000
          - 00:05:00
          - 9000
          - 300s
          - 300.0
        """
        input = input.strip()
        if input.isdigit():
            timecode = int(input)
            if timecode < 0:
                raise ValueError('Timecode frame number must be positive.')
            return timecode
        
        elif input.find(':') >= 0:
            values = input.split(":")
            hrs, mins = int(values[0]), int(values[1])
            secs = float(values[2]) if '.' in values[2] else int(values[2])
            if not (hrs >= 0 and mins >= 0 and secs >= 0 and mins < 60 and secs < 60):
                raise ValueError('Invalid timecode range (values outside allowed range).')
            secs += (hrs * 60 * 60) + (mins * 60)
            return self._seconds_to_frames(secs)

        if input.endswith('s'):
            input = input[:-1]
        
        if not input.replace('.', '').isdigit():
            raise ValueError('All characters in timecode seconds string must be digits.')

        as_float = float(input)
        if as_float < 0.0:
            raise ValueError('Timecode seconds value must be positive.')
        return self._seconds_to_frames(as_float)

    def _parse_timecode_number(self, timecode: Union[int, float]) -> int:
        """
        Parse the timecode number into the exact number of frames.
        """
        if isinstance(timecode, int): # the number of frames N
            if timecode < 0:
                raise ValueError('Timecode frame number must be positive and greater than zero.')
            return timecode
        
        elif isinstance(timecode, float): # secs
            if timecode < 0.0:
                raise ValueError('Timecode value must be positive and greater than zero.')

        elif isinstance(timecode, FrameTimecode):
            return timecode.frame_num
        
        elif timecode is None:
            raise TypeError('Timecode/frame number must be specified!')
        else:
            raise TypeError('Timecode format/type unrecognized.')
    
    def _seconds_to_frames(self, seconds: float) -> int:
        return round(seconds * self.framerate)

    def __iadd__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            self.frame_num += other
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num += other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        elif isinstance(other, float):
            self.frame_num += self._seconds_to_frames(other)
        elif isinstance(other, str):
            self.frame_num += self._parse_timecode_string(other)
        else:
            raise TypeError('Unsupported type for addition. {}'.format(type))
        if self.frame_num < 0:
            self.frame_num = 0
        return self

    def __add__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        to_return = FrameTimecode(timecode=self)
        to_return += other
        return to_return

    def __isub__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            self.frame_num -= other
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num -= other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        elif isinstance(other, float):
            self.frame_num -= self._seconds_to_frames(other)
        elif isinstance(other, str):
            self.frame_num -= self._parse_timecode_string(other)
        else:
            raise TypeError('Unsupported type for addition: {}'.format(type))
        if self.frame_num < 0:
            self.frame_num = 0
        return self

    def __sub__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        to_return = FrameTimecode(timecode=self)
        to_return -= other
        return to_return

    def __eq__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            return self.frame_num == other
        elif isinstance(other, float):
            return self.get_seconds() == other
        elif isinstance(other, str):
            return self.frame_num == self._parse_timecode_string(other)
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num == other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        elif other is None:
            return False
        else:
            raise TypeError('Unsupported type for performing equal: {}'.format(other))

    def __ne__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        return not self == other
    
    def __lt__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            return self.frame_num < other
        elif isinstance(other, float):
            return self.get_seconds() < other
        elif isinstance(other, str):
            return self.frame_num < self._parse_timecode_string(other)
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num < other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        else:
            raise TypeError('Unsupported type for performing equal: {}'.format(other))

    def __lt__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            return self.frame_num <= other
        elif isinstance(other, float):
            return self.get_seconds() <= other
        elif isinstance(other, str):
            return self.frame_num <= self._parse_timecode_string(other)
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num <= other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        else:
            raise TypeError('Unsupported type for performing equal: {}'.format(other))

    def __gt__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            return self.frame_num > other
        elif isinstance(other, float):
            return self.get_seconds() > other
        elif isinstance(other, str):
            return self.frame_num > self._parse_timecode_string(other)
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num > other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        else:
            raise TypeError('Unsupported type for performing equal: {}'.format(other))

    def __ge__(self, other: Union[int, float, str, 'FrameTimecode']) -> 'FrameTimecode':
        if isinstance(other, int):
            return self.frame_num >= other
        elif isinstance(other, float):
            return self.get_seconds() >= other
        elif isinstance(other, str):
            return self.frame_num >= self._parse_timecode_string(other)
        elif isinstance(other, FrameTimecode):
            if self.equal_framerate(other.framerate):
                self.frame_num >= other.frame_num
            else:
                raise ValueError('FrameTimecode instances require equal framerate for subtraction.')
        else:
            raise TypeError('Unsupported type for performing equal: {}'.format(other))

    def __int__(self) -> int:
        return self.frame_num
    
    def __float__(self) -> float:
        return self.seconds
    
    def __str__(self) -> str:
        return self.timecode
    
    def __repr__(self) -> str:
        return '{} [frame={:d}, fps={:.3f}]'.format(self.timecode, self.frame_num, self.framerate)
    
    def __hash__(self) -> int:
        return self.frame_num