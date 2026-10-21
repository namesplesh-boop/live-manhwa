from moviepy import VideoFileClip, concatenate_videoclips
from pathlib import Path
import sys
import os
import time
from google import genai
import replicate
from google.genai import types
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
load_dotenv()
PROMPT = """Animate this manhwa illustration as a living motion-comic shot. Bring the scene gently to life while keeping every drawn detail fully intact.
DO:

Slow, smooth cinematic push-in — a gentle Ken Burns zoom toward the main character
Layered parallax: foreground, character, and background drift at slightly different depths
Mood-matched ambient particles — warm glowing bokeh for tender scenes, drifting fire embers and sparks for dark or tense scenes
Soft hair and cloth sway, gentle atmospheric light shimmer and glow

CAMERA:

Slow, deliberate, smooth — push-in or soft drift, never shaky or fast

KEEP:

Original art, colors, and linework sharp and intact at all times
Use only colors and effects already present in the image — no new hues

NEVER DO:

No eye movement, no blinking — eyes completely static
No pose, expression, or facial changes, no morphing
No completing cropped body parts — the frame edge is absolute
No new elements, no text, no cursors, no audio"""

def main():
    try:
        print("Token found:", bool(os.getenv("REPLICATE_API_TOKEN")))
        print("Token found:", bool(os.getenv("GEMINI_API_KEY")))
        Path("upscaled").mkdir(exist_ok=True)
        Path("videos").mkdir(exist_ok=True)
        Path("final_video").mkdir(exist_ok=True)

        screens = get_files("screenshots", (".jpg", ".jpeg", ".png"))
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.map(upscale, screens)

        upscaled = get_files("upscaled", (".jpg", ".jpeg", ".png"))
        client = genai.Client()
        def safe_gen_video(image):
            try:
                gen_video(image, client)
            except Exception as e:
                print(f"Failed: {image.name} - {e}")
        with ThreadPoolExecutor(max_workers=4) as pool:
            pool.map(safe_gen_video, upscaled)
        client.close()

        videos = get_files("videos", (".mp4",))
        videos_sorted = sort_files(videos)
        video_create(videos_sorted, "final_video/final_video.mp4")
        print("This is the end!")



    except FileNotFoundError:
        print("Folder not found")
    except ValueError as e:
        sys.exit(e)

# receiving and filtering files
def get_files(folder, extensions):
    screens = Path(folder)
    clear_file = []
    if len(list(screens.iterdir())) == 0:
         raise ValueError("Folder is empty")
    for screen in screens.iterdir():
        if screen.suffix.lower() not in extensions:
            print(f"Skipped: {screen.name}")
        else:
            clear_file.append(screen)
    print("Success get_files")
    return clear_file

# sorting files in folders
def sort_files(folder):
    return sorted(folder, key=lambda file: int(file.stem))


# improving screenshot quality
def upscale(screen):
    for attempt in range(3):
        try:
            with open(screen, "rb") as image:
                output = replicate.run("cjwbw/real-esrgan:d0ee3d708c9b911f122a4ad90046c5d26a0293b99476d697f6bb7f2e251ce2d4", input={"image": image})

            with open(Path("upscaled")/screen.name, "wb") as file:
                file.write(output.read())
            return print(f"Upscaled: {screen.name}")
        except Exception as e:
            print(f"ERROR {screen.name} Try {attempt + 1}: {type(e).__name__}: {e}")
            time.sleep(15)
    print(f"ERROR {screen.name}: all attempts unsuccessful")

def gen_video(screen_upscale, client):
    print("gen_video start")
    image = types.Image.from_file(location=str(screen_upscale))

    # Generate video with Veo 3.1 using the image.
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        source=types.GenerateVideosSource(
            # Prompt is optional if image is provided
            image=image,
            prompt=PROMPT
        ),
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            duration_seconds=4,
            aspectRatio="16:9",
            resolution="720p"
        ),
    )


    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the video.
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video, destination=Path(f"videos") / f"{screen_upscale.stem}.mp4")
    print(f"Generated video saved to {screen_upscale.stem}.mp4")
    print("gen_video end")

def video_create(folder, output):
    videos = []
    for video in folder:
        clip = VideoFileClip(f"{video}")
        videos.append(clip)

    # We concatenate them and write the result
    final_clip = concatenate_videoclips(videos)
    final_clip.write_videofile(output)


if __name__ == "__main__":
    main()
