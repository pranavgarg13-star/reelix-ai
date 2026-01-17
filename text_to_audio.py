import os
from gtts import gTTS


def text_to_speech_file(text: str, folder: str) -> str:
    """
    Converts text to speech using Google Text-to-Speech (gTTS)
    and saves the audio as audio.mp3 inside user_uploads/<folder>/
    """

    # 1️⃣ Ensure the user folder exists
    folder_path = os.path.join("user_uploads", folder)
    os.makedirs(folder_path, exist_ok=True)

    # 2️⃣ Output file path
    save_file_path = os.path.join(folder_path, "audio.mp3")

    # 3️⃣ Generate audio using gTTS
    tts = gTTS(
        text=text,
        lang="en",     # language
        slow=False     # normal speed
    )

    # 4️⃣ Save audio file
    tts.save(save_file_path)

    print(f"{save_file_path}: Audio file saved successfully!")

    # 5️⃣ Return file path
    return save_file_path


# # ✅ TEST (run this file directly)
# if __name__ == "__main__":
#     text_to_speech_file(
#         "Hey I am a good boy and this is the python course",
#         "ac9a7034-2bf9-11f0-b9c0-ad551e1c593a"
#     )
# used google translate
