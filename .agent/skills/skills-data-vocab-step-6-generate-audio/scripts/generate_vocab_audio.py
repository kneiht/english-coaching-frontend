#!/usr/bin/env python3
"""
Generate vocabulary audio files from vocab.json using Gemini TTS.

Reads vocab.json and generates two audio files per word:
  - audio/{word}.mp3        (reads the English word only)
  - audio/{word}-sentence.mp3 (reads the example sentence)

Requirements:
  - pip install google-genai python-dotenv pydub
  - ffmpeg installed (for wav -> mp3 conversion)
  - GOOGLE_API_KEY in .env
"""
import argparse
import json
import os
import sys
import time
import wave
import tempfile

from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


# Neutral director notes — read plainly without acting or emotion
DIRECTOR_NOTES = (
    "Director's Notes: Read the text in a plain, neutral, clear voice. "
    "Do NOT add any emotion, whispering, excitement, or dramatic effect. "
    "Do NOT interpret the meaning of words — just read them clearly and evenly. "
    "Accent: Standard American English. Speed: Normal. Tone: Neutral and even."
)

VOICE_NAME = "Kore"
MODEL_ID = "gemini-2.5-flash-preview-tts"


def save_wave(filename: str, pcm_data: bytes, rate: int = 24000) -> None:
    """Save raw PCM data as a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def wav_to_mp3(wav_path: str, mp3_path: str) -> None:
    """Convert WAV to MP3 using pydub/ffmpeg."""
    if not HAS_PYDUB:
        raise RuntimeError("pydub not installed. Run: pip install pydub")
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3", bitrate="128k")


def generate_tts(client, text: str, output_mp3: str) -> tuple[bool, str]:
    """
    Generate TTS for given text and save as MP3.
    Returns (success, error_message).
    """
    prompt = f"{DIRECTOR_NOTES}\n\nTranscript: {text}"

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=VOICE_NAME
                        )
                    )
                ),
            ),
        )

        # Extract audio data
        audio_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                audio_data = part.inline_data.data
                break

        if not audio_data:
            return False, "No audio data in response"

        # Save as WAV then convert to MP3
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name

        save_wave(tmp_wav, audio_data)
        os.makedirs(os.path.dirname(output_mp3) or ".", exist_ok=True)
        wav_to_mp3(tmp_wav, output_mp3)
        os.unlink(tmp_wav)

        return True, ""

    except Exception as e:
        return False, str(e)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate vocabulary audio from vocab.json using Gemini TTS."
    )
    parser.add_argument(
        "vocab_json",
        help="Path to vocab.json file"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for audio files (default: audio/ next to vocab.json)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing audio files"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Seconds to wait between API calls (default: 5)"
    )
    parser.add_argument(
        "--word-only",
        action="store_true",
        help="Only generate word audio, skip sentences"
    )
    parser.add_argument(
        "--sentence-only",
        action="store_true",
        help="Only generate sentence audio, skip words"
    )
    args = parser.parse_args()

    # Load vocab.json
    vocab_path = os.path.abspath(args.vocab_json)
    if not os.path.exists(vocab_path):
        print(f"❌ File not found: {vocab_path}")
        sys.exit(1)

    with open(vocab_path, "r", encoding="utf-8") as f:
        groups = json.load(f)

    # Determine output directory
    vocab_dir = os.path.dirname(vocab_path)
    audio_dir = args.output_dir or os.path.join(vocab_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    # Init Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Collect all tasks
    tasks = []
    for group in groups:
        for word in group["words"]:
            audio_word_path = word.get("audio_word", "")
            audio_sentence_path = word.get("audio_sentence", "")
            english_word = word["english_word"]
            example_en = word.get("example_sentence_en", "")

            # Word audio
            if audio_word_path and not args.sentence_only:
                filename = os.path.basename(audio_word_path)
                full_path = os.path.join(audio_dir, filename)
                tasks.append({
                    "type": "word",
                    "text": english_word,
                    "output": full_path,
                    "label": f"{english_word} (word)",
                })

            # Sentence audio
            if audio_sentence_path and example_en and not args.word_only:
                filename = os.path.basename(audio_sentence_path)
                full_path = os.path.join(audio_dir, filename)
                tasks.append({
                    "type": "sentence",
                    "text": example_en,
                    "output": full_path,
                    "label": f"{english_word} (sentence)",
                })

    print(f"📋 Total tasks: {len(tasks)}")
    print(f"📂 Output: {audio_dir}")
    print(f"⏱️  Delay: {args.delay}s between calls")
    print()

    # Log files
    log_path = os.path.join(audio_dir, "_generation.log")
    error_log_path = os.path.join(audio_dir, "_error.log")

    success_count = 0
    skip_count = 0
    error_count = 0

    with open(log_path, "a", encoding="utf-8") as log_f, \
         open(error_log_path, "a", encoding="utf-8") as err_f:

        from datetime import datetime
        log_f.write(f"\n=== Run started at {datetime.now().isoformat()} ===\n")

        for idx, task in enumerate(tasks):
            output = task["output"]
            label = task["label"]

            # Skip existing
            if os.path.exists(output) and not args.overwrite:
                msg = f"  [{idx+1}/{len(tasks)}] SKIPPED (exists): {label}"
                print(msg)
                log_f.write(msg + "\n")
                skip_count += 1
                continue

            msg = f"  [{idx+1}/{len(tasks)}] Generating: {label}"
            print(msg)
            log_f.write(msg + "\n")
            log_f.flush()

            ok, error = generate_tts(client, task["text"], output)

            if ok:
                print(f"      -> ✅ {os.path.basename(output)}")
                log_f.write(f"      -> ✅ {output}\n")
                success_count += 1
            else:
                print(f"      -> ❌ {error}")
                log_f.write(f"      -> ❌ {error}\n")
                err_f.write(f"[{datetime.now().isoformat()}] {label}\n")
                err_f.write(f"  text: {task['text']}\n")
                err_f.write(f"  error: {error}\n\n")
                err_f.flush()
                error_count += 1

            # Delay between API calls
            if idx < len(tasks) - 1:
                time.sleep(args.delay)

    print(f"\n{'='*50}")
    print(f"✅ Success: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"❌ Errors:  {error_count}")
    print(f"📄 Log: {log_path}")
    print(f"📄 Error log: {error_log_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
