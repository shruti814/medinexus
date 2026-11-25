import os
import whisper


def transcribe_audio(audio_file, model_name="base"):

    if not os.path.exists(audio_file):

        raise FileNotFoundError("Audio file not found")

    model = whisper.load_model(model_name)

    result = model.transcribe(audio_file)

    return result.get("text", "").strip()


if __name__ == "__main__":

    audio_file = "test_audio.mp3"

    text = transcribe_audio(audio_file)

    print(text)