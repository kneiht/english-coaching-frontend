#!/usr/bin/env python3
"""
Generate reading lesson audio files using Gemini TTS.

Reads a JSON config with paragraph texts and generates audio for each.

Requirements:
  - pip install google-genai python-dotenv pydub
  - ffmpeg installed (for wav -> mp3 / wav conversion)
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


# Director notes for reading paragraphs — clear, even pace
DIRECTOR_NOTES = (
    "Director's Notes: Read the following paragraph clearly and at a moderate pace. "
    "Use natural pauses at commas and periods. "
    "Do NOT add dramatic effects or exaggerated intonation. "
    "Accent: Standard American English. Speed: Slightly slower than normal, suitable for ESL learners. "
    "Tone: Warm, clear, and educational."
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


def generate_tts(client, text: str, output_path: str) -> tuple:
    """
    Generate TTS for given text and save as WAV.
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

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Save as WAV
        save_wave(output_path, audio_data)

        return True, ""

    except Exception as e:
        return False, str(e)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate reading lesson audio using Gemini TTS."
    )
    parser.add_argument(
        "config_json",
        help="Path to JSON config file with paragraphs to generate audio for"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for audio files"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing audio files"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Seconds to wait between API calls (default: 10)"
    )
    args = parser.parse_args()

    # Load config
    config_path = os.path.abspath(args.config_json)
    if not os.path.exists(config_path):
        print(f"❌ File not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        paragraphs = json.load(f)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Init Gemini client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print(f"📋 Total paragraphs: {len(paragraphs)}")
    print(f"📂 Output: {output_dir}")
    print(f"⏱️  Delay: {args.delay}s between calls")
    print()

    success_count = 0
    skip_count = 0
    error_count = 0

    for idx, item in enumerate(paragraphs):
        filename = item["filename"]
        text = item["text"]
        output_path = os.path.join(output_dir, filename)

        # Skip existing
        if os.path.exists(output_path) and not args.overwrite:
            print(f"  [{idx+1}/{len(paragraphs)}] SKIPPED (exists): {filename}")
            skip_count += 1
            continue

        print(f"  [{idx+1}/{len(paragraphs)}] Generating: {filename}")
        print(f"      Text: {text[:80]}...")

        ok, error = generate_tts(client, text, output_path)

        if ok:
            print(f"      -> ✅ {filename}")
            success_count += 1
        else:
            print(f"      -> ❌ {error}")
            error_count += 1

        # Delay between API calls
        if idx < len(paragraphs) - 1:
            time.sleep(args.delay)

    print(f"\n{'='*50}")
    print(f"✅ Success: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"❌ Errors:  {error_count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
