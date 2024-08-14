import argparse

from typing import Optional
from video_stream import VideoStreamCv2

def open_video(
    input_path: str,
    framerate: Optional[float] = None,
) -> VideoStreamCv2:
    try:
        return VideoStreamCv2(input_path, framerate)
    except:
        raise Exception('Failed to open video')

def main(input_path: str):
    video = open_video(input_path)
    import ipdb; ipdb.set_trace()
    # detector = ContentDetector()
    # scene_manager = SceneManager()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', '-i', type=str, required=True, help="input video path")
    args = parser.parse_args()
    main(args.input_path)