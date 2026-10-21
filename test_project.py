from project import get_files, sort_files, video_create
from moviepy import ColorClip, VideoFileClip
from pathlib import Path
import pytest

def test_get_files(tmp_path):
    with pytest.raises(ValueError):
            get_files(tmp_path, (".jpg", ".jpeg", ".png"))
    (tmp_path / "1.png").touch()
    (tmp_path / "9.png").touch()
    (tmp_path / "notes.txt").touch()
    files = get_files(tmp_path, (".jpg", ".jpeg", ".png"))
    name = sorted(f.name for f in files)
    assert name == ["1.png", "9.png"]

def test_sort_files():
    folder = [Path("1.png"), Path("10.png"), Path("0.png")]
    assert sort_files(folder) == [Path("0.png"),Path("1.png"), Path("10.png")]

def test_video_create(tmp_path):
    clip = ColorClip(size=(64, 64), color=(255, 0, 0), duration=1)
    clip.write_videofile(str(tmp_path/"1.mp4"), fps=24)
    clip = ColorClip(size=(64, 64), color=(255, 0, 0), duration=1)
    clip.write_videofile(str(tmp_path/"10.mp4"), fps=24)
    folder = []
    folder.append(str(tmp_path/"1.mp4"))
    folder.append(str(tmp_path/"10.mp4"))
    output = tmp_path / "final.mp4"
    video_create(folder, output)
    assert output.exists()
    with VideoFileClip(str(output)) as result:
         assert round(result.duration) == 2
