import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

import os
import time
import subprocess
from text_to_audio import text_to_speech_file

load_dotenv()
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)


def text_to_audio(folder):
    print("TTA - ", folder)

    desc = f"user_uploads/{folder}/desc.txt"
    if not os.path.exists(desc):
        print("desc.txt missing")
        return False

    with open(desc, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("desc.txt empty")
        return False
    
    result = text_to_speech_file(text, folder)
    if result is None:
       print("Audio generation failed, skipping reel")
    return False


def download_images(folder):
    import requests
    base = f"user_uploads/{folder}"
    os.makedirs(base, exist_ok=True)

    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix=f"reelix/{folder}/",
            max_results=50
        )
        resources = sorted(result["resources"], key=lambda x: x["public_id"])
    except Exception as e:
        print(f"Cloudinary fetch failed: {e}")
        return False

    if not resources:
        print("No images found on Cloudinary")
        return False

    for i, resource in enumerate(resources, 1):
        url = resource["secure_url"]
        ext = url.split(".")[-1].split("?")[0]
        filepath = os.path.join(base, f"img_{i}.{ext}")
        try:
            response = requests.get(url, timeout=30)
            with open(filepath, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"Failed to download image {url}: {e}")
            return False

    return True   
    
   
def create_input_file(folder):
    base = f"user_uploads/{folder}"
    images = sorted([
        f for f in os.listdir(base)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])

    if not images:
        print("No images found")
        return False

    input_txt = os.path.join(base, "input.txt")

    with open(input_txt, "w", encoding="utf-8") as f:
        for img in images:
            full = os.path.abspath(os.path.join(base, img))
            full = full.replace("\\", "/")
            f.write(f"file '{full}'\n")
            f.write("duration 1\n")

        # FFmpeg concat demuxer requires the last file to be written
        # again without a duration to properly terminate the stream
        f.write(f"file '{full}'\n")

    return True


def create_reel(folder):
    base = f"user_uploads/{folder}"

    if not os.path.exists(f"{base}/audio.mp3"):
        print("audio.mp3 missing")
        return

    if not create_input_file(folder):
        print("input.txt failed")
        return

    out = f"static/reels/{folder}.mp4"

    cmd = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", f"{base}/input.txt",
    "-i", f"{base}/audio.mp3",
    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
    "-c:v", "libx264",
    "-c:a", "aac",
    "-shortest",
    "-r", "30",
    "-pix_fmt", "yuv420p",
    out ]

    
    try:
       subprocess.run(cmd, shell=False, check=True, timeout=120)
       print("Video created:", out)
       try:
           cloudinary.uploader.upload(
        out,
        folder="reelix/reels",
        public_id=folder,
        resource_type="video",
        overwrite=True
    )
           print("Video uploaded to Cloudinary")
       except Exception as e:
             print(f"Cloudinary upload failed: {e}")
    except subprocess.TimeoutExpired:
       print("FFmpeg timed out")
    except subprocess.CalledProcessError as e:
       print(f"FFmpeg failed: {e}")

def run_worker():
    while True:
        print("Processing queue...")

        if not os.path.exists("done.txt"):
            open("done.txt", "w").close()

        with open("done.txt") as f:
            done = [x.strip() for x in f.readlines()]

        folders = os.listdir("user_uploads") if os.path.exists("user_uploads") else []
        print(f"Found folders: {folders}")

        for folder in folders:
            if folder in done:
                continue

            try:
                if download_images(folder) and text_to_audio(folder):
                    create_reel(folder)
                with open("done.txt", "a") as f:
                    f.write(folder + "\n")
            except Exception as e:
                print(f"Failed to process {folder}: {e}")

        time.sleep(4)

if __name__ == "__main__":
    run_worker()
