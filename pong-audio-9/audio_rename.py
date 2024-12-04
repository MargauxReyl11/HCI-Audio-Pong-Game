#https://www.geeksforgeeks.org/convert-text-speech-python/
from gtts import gTTS
import os

sentences = {
    "welcome": "Thanks for playing Pong! Match pitch to move your paddle and get the ball! Say start to start playing, say pause in order to pause any time. Change levels by saying easy level, hard level, or insane level. While playing, say power up if you want to use the powers available. Say instructions if you would like to hear this message again. Good luck",
}

language = 'en'


output_directory = "audio_files"
os.makedirs(output_directory, exist_ok=True)

for filename, text in sentences.items():
    print(f"Generating audio for: {filename}")
    tts = gTTS(text=text, lang=language, slow=False)
    filepath = os.path.join(output_directory, f"{filename}.mp3")
    tts.save(filepath)

print(f"Audio files have been saved in the '{output_directory}' directory.")