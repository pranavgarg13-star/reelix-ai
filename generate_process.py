

import os
import time
import subprocess
from text_to_audio import text_to_speech_file

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

    text_to_speech_file(text, folder)
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

    cmd = (
        f'ffmpeg -y -f concat -safe 0 '
        f'-i "{base}/input.txt" '
        f'-i "{base}/audio.mp3" '
        f'-vf "scale=1080:1920:force_original_aspect_ratio=decrease,'
        f'pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" '
        f'-c:v libx264 -c:a aac -shortest -r 30 '
        f'-pix_fmt yuv420p "{out}"'
    )

    subprocess.run(cmd, shell=True, check=True)
    print("Video created:", out)


if __name__ == "__main__":
    while True:
        print("Processing queue...")

        if not os.path.exists("done.txt"):
            open("done.txt", "w").close()

        with open("done.txt") as f:
            done = [x.strip() for x in f.readlines()]

        for folder in os.listdir("user_uploads"):
            if folder in done:
                continue

            if text_to_audio(folder):
                create_reel(folder)

                with open("done.txt", "a") as f:
                    f.write(folder + "\n")

        time.sleep(4)

