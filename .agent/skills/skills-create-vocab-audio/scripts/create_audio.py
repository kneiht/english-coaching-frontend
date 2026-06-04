#!/usr/bin/env python3
import os
import sys
import json
import glob

# Add project root to path to import tts_gemini
sys.path.append(os.getcwd())

try:
    from tts_gemini import GeminiTTS
except ImportError:
    print("❌ Error: Could not import tts_gemini. Make sure you run this script from the project root.")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_audio.py <path_to_unit_dir>")
        sys.exit(1)

    unit_dir = sys.argv[1]
    if not os.path.isdir(unit_dir):
        print(f"❌ Error: {unit_dir} is not a valid directory.")
        sys.exit(1)

    # Find all lesson-*-vocab.json files
    vocab_files = sorted(glob.glob(os.path.join(unit_dir, "lesson-*-vocab.json")))
    if not vocab_files:
        print(f"⚠️ No lesson-*-vocab.json files found in {unit_dir}")
        sys.exit(0)

    print(f"🔍 Found {len(vocab_files)} vocab JSON files to process.")
    
    try:
        tts = GeminiTTS()
    except Exception as e:
        print(f"❌ Failed to initialize GeminiTTS: {e}")
        sys.exit(1)

    for vf in vocab_files:
        print(f"\n📖 Processing file: {vf}")
        try:
            with open(vf, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # The JSON file starts with a wrapper key like "lesson-1-vocab"
            # Let's extract the inside data
            root_key = list(data.keys())[0]
            lesson_data = data[root_key]
            
            tts.process_vocab_json(
                lesson_data,
                words_dir=os.path.join(unit_dir, "audio-words"),
                sentences_dir=os.path.join(unit_dir, "audio-sentences")
            )
        except Exception as err:
            print(f"❌ Error processing {vf}: {err}")

    print("\n🎉 Completed audio generation for all vocab files.")

if __name__ == "__main__":
    main()
