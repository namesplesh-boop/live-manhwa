# Live Manhwa
#### Video Demo: https://youtu.be/FUEmvo1tN2M
#### Description:
## Overview
The program optimizes and partially automates the process of creating animated manhwa. It takes manhwa screenshots that were downloaded in advance, upscales them to an acceptable quality, generates short video clips from each image, and then merges the clips into one long video.
## How it works
Overall, the video creation process consists of four main stages: reading screenshots, upscaling, video generation, and merging.

First, the program checks that all API keys are configured correctly. Then it creates all the folders needed for the work, skipping any that already exist. Next, the files are checked for a supported format, and the folder is checked to make sure it is not empty. If everything is in order, the program builds a list of files.

After that, the upscale function runs. It can optionally run in multiple threads. It sends the screenshots through the API to Replicate, where they are upscaled and saved to a new folder.

Then the program builds a new list from the upscaled folder. It initializes the Gemini client and starts video generation in multiple threads to speed up the process, using a universal prompt prepared in advance. The resulting clips are saved to a separate folder, and the client is closed.

Finally, the program collects the newly created videos, sorts them, and merges them into one long sequential video, which is saved to the `final_video` folder.
## Files
### `project.py`
The main program. It contains:
- `main()` - The core code takes screenshots and converts them into the final video.
- `get_files(folder, extensions)` - receives a folder containing photos or videos, checks their format, discards empty folders, and returns a variable containing the files that is ready for use by the code.
- `sort_files(files)` - sorts files in a folder in ascending order
- `upscale(screen)` - improves screenshot quality
- `gen_video(screen_upscale, client)` - generates video from photos
- `video_create(files, output)` - creates the final video
### `test_project.py`
Tests for the functions that do not need an API key:
- `test_get_files(tmp_path)` - tests `get_files` for filtering out unsuitable file formats
- `test_sort_files` - tests `sort_files` for the ability to sort in the correct order
- `test_video_create` - tests `video_create` for the ability to stitch videos together sequentially, one after another

### `requirements.txt`
The list of libraries needed to run the project.

### `.env` (not included)
Stores the API keys. You need to create it yourself with two variables:
`REPLICATE_API_TOKEN` and `GEMINI_API_KEY`.

### Folders
- `screenshots/` — input images
- `upscaled/` — enhanced screenshots
- `videos/` — video made from screenshots
- `final_video/` — the final video is made from short videos.
## Setup
1. Install the required libraries:
```
   pip install -r requirements.txt
```
2. Create a `.env` file in the project folder with your API keys:
```
   REPLICATE_API_TOKEN=your_replicate_token
   GEMINI_API_KEY=your_gemini_key
```
3. Put the manhwa screenshots into the `screenshots` folder.
   File names must be numbers (`1.png`, `2.png`, ...) so they can be sorted.
4. Run the program:
```
   python project.py
```
## Design choices
**One thread for upscaling, four for video generation**

Replicate allows only one request at a time until the account has at least $5 in credit. I decided not to top up the balance, but I kept the multithreading code so it can be used in the future by simply increasing `max_workers`. For video generation, my Gemini account already supports several requests at once, so I took the opportunity to run it in multiple threads and speed up the process.

**Several attempts with a pause in `upscale`**
I added retries for failed requests so that a temporary API error does not cause a screenshot to be skipped. The pause between attempts is needed to avoid errors caused by sending requests too often.

**Wrapper function `safe_gen_video` for multithreading**
`pool.map` passes only one argument at a time to the function it runs the next item from the list. But `gen_video` needs two arguments: the image and the Gemini client. So I created a small wrapper function inside `main()` that takes only the image and gets the client from `main()` itself. The wrapper also catches errors, so if one video fails (for example, blocked by Veo's safety filter), the other videos keep generating instead of the whole program stopping.

**API keys in a `.env` file**
To avoid exposing my API keys when sharing or submitting the code, I stored them in a separate `.env` file instead of writing them directly in `project.py`. The keys are loaded automatically at startup with `load_dotenv()` from the `python-dotenv` library, so the code itself never contains them. The `.env` file is not included in the submission, and anyone who wants to run the project can create their own with their own keys.

**The Gemini client is created inside `main()`**
This prevents the client from being created every time the file is imported during testing. Otherwise, `pytest` would fail without an API key. The second reason is that `safe_gen_video` needs the client to work properly, and since both are inside `main()`, the wrapper can use it directly.

**Sorting files before merging**
To make sure the final video is merged in the correct order, I use the `sort_files()` function, which sorts the list of files in ascending order. Files are sorted by the number in their name, not as text — otherwise `10.mp4` would come before `2.mp4`.

**File extensions as a parameter of `get_files`.**
For readability and convenience, I made one universal `get_files` function for both images and videos. Depending on which file type I need, i pass the matching extensions as a parameter for videos, ".mp4" or ".jpg", ".jpeg", ".png".

**Real-ESRGAN for upscaling and Veo for video generation.**
I chose Real-ESRGAN on Replicate because it is extremely cheap and does not require a subscription you only pay per run. I chose Google Veo because, in my experience, it gives the best quality among similar tools at a reasonable price, which makes it the optimal choice for this project.
## Limitations
**API safety filters.** The main problem is that API safety filters can unexpectedly reject the generation of an image or video. Sometimes a retry helps, but more often it does not, and the only solution is to change the prompt manually or edit the image by hand so that it passes the filter.

**No automatic quality control.** The program cannot check the quality of the generated videos by itself. Sometimes Veo produces hallucinations, which can be explained by using one universal prompt instead of a prompt tailored to each image. A good improvement would be an AI agent that reviews every video and, if it finds hallucinations, either regenerates that video or writes an individual prompt for it.

**Missing clips are skipped.** If at least one image or video fails to generate, the final video is still created, but it simply skips the missing parts.
