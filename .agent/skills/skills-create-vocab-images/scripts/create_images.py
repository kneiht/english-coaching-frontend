#!/usr/bin/env python3
import os
import sys
import json
import glob
import time
import random
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from project root .env
load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Error: google-genai is not installed. Install with: pip install google-genai")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("❌ Error: Pillow is not installed. Install with: pip install Pillow")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_images.py <path_to_unit_dir>")
        sys.exit(1)

    unit_dir = sys.argv[1]
    if not os.path.isdir(unit_dir):
        print(f"❌ Error: {unit_dir} is not a valid directory.")
        sys.exit(1)

    # Output directory
    output_dir = os.path.abspath(os.path.join(unit_dir, "images-words"))
    os.makedirs(output_dir, exist_ok=True)

    # Find all vocab JSON files
    vocab_files = sorted(glob.glob(os.path.join(unit_dir, "lesson-*-vocab.json")))
    if not vocab_files:
        print(f"⚠️ No lesson-*-vocab.json files found in {unit_dir}")
        sys.exit(0)

    # 1. Collect all vocab words that need images
    words_to_generate = []
    for vf in vocab_files:
        try:
            with open(vf, "r", encoding="utf-8") as f:
                data = json.load(f)
            root_key = list(data.keys())[0]
            vocab_list = data[root_key].get("vocab", [])
            for item in vocab_list:
                word = item.get("word")
                image_url = item.get("image")
                if not word or not image_url:
                    continue
                
                # Get the target filename (e.g. affect.webp)
                filename = os.path.basename(image_url)
                target_path = os.path.join(output_dir, filename)
                
                if os.path.exists(target_path):
                    print(f"⏩ Skipping existing image: {filename}")
                else:
                    words_to_generate.append({
                        "word": word,
                        "meaning": item.get("vietnameseMeaning", ""),
                        "sentence": item.get("sampleSentence", ""),
                        "filename": filename
                    })
        except Exception as err:
            print(f"❌ Error reading {vf}: {err}")

    if not words_to_generate:
        print("✨ All vocabulary images already exist. Nothing to generate!")
        sys.exit(0)

    print(f"🔍 Found {len(words_to_generate)} images to generate.")

    # 2. Batch generate prompts using Gemini API
    print("🤖 Generating prompts using Gemini...")
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        sys.exit(1)
        
    client = genai.Client(api_key=google_api_key)
    
    vocab_str = json.dumps(words_to_generate, ensure_ascii=False, indent=2)
    prompt_request = f"""
You are a prompt engineer for an AI image generator (Imagen 3).
Here is a list of vocabulary words and meanings for an English lesson.
For each word, write a highly descriptive visual prompt suitable for learning.
The prompt must describe a photorealistic, high-detail scene representing the word, and end with "highly detailed, photorealistic, 8k, don't add any text to the image".
Avoid any text, labels, or watermarks in the image.

Vocabulary List:
{vocab_str}

Output a valid JSON array of objects. Do NOT include markdown formatting (do not wrap in ```json). Follow this JSON schema exactly:
[
  {{
    "filename": "word-file.webp",
    "prompt": "prompt description here"
  }}
]
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_request,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        prompts_list = json.loads(response.text)
    except Exception as e:
        print(f"❌ Failed to generate prompts using Gemini: {e}")
        sys.exit(1)

    print(f"✅ Generated {len(prompts_list)} prompts.")

    # 3. Generate images using gemini_image_gen.py
    image_gen_script = "/Users/kay/KAY/Coding/chill-labs/chill-teacher-lesons-data/tools/gemini_image_gen.py"
    if not os.path.exists(image_gen_script):
        print(f"❌ Error: Image generator script not found at {image_gen_script}")
        sys.exit(1)

    # Make sure we have cookie
    if not os.environ.get("GEMINI_SECURE_1PSID"):
        print("❌ Error: GEMINI_SECURE_1PSID not found in .env file.")
        sys.exit(1)

    for idx, item in enumerate(prompts_list):
        filename = item.get("filename")
        prompt_text = item.get("prompt")
        if not filename or not prompt_text:
            continue

        prefix = os.path.splitext(filename)[0]
        final_webp_path = os.path.join(output_dir, filename)

        print(f"\n🎨 [{idx+1}/{len(prompts_list)}] Generating: {filename}")
        
        # Call gemini_image_gen.py via poetry in the lessons-data project
        # It expects: poetry run python3 tools/gemini_image_gen.py "Generate ... Aspect ratio: 16:9." -o output_dir -p prefix
        cmd = [
            "poetry", "run", "python3", "tools/gemini_image_gen.py",
            f"Generate {prompt_text} Aspect ratio: 16:9.",
            "-o", output_dir,
            "-p", prefix
        ]

        try:
            # Run the command inside the lessons-data project folder where poetry is configured
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=os.environ,
                cwd="/Users/kay/KAY/Coding/chill-labs/chill-teacher-lesons-data"
            )
            if res.returncode != 0:
                print(f"❌ Error generating image: {res.stderr.strip() or res.stdout.strip()}")
                continue


            # gemini_image_gen.py saves as prefix_0.png
            png_file = os.path.join(output_dir, f"{prefix}_0.png")
            if os.path.exists(png_file):
                # Convert PNG to WEBP
                with Image.open(png_file) as img:
                    img.save(final_webp_path, "WEBP", quality=90)
                os.remove(png_file)
                print(f"✅ Saved image to: {final_webp_path}")
            else:
                print(f"❌ Expected output file {png_file} was not found.")

        except Exception as e:
            print(f"❌ Subprocess execution failed: {e}")

        # Delay to prevent rate limiting
        if idx < len(prompts_list) - 1:
            delay = random.randint(10, 15)
            print(f"Waiting {delay} seconds before next image...")
            time.sleep(delay)

    print("\n🎉 Completed image generation for all vocabulary words.")

if __name__ == "__main__":
    main()
