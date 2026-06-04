#!/usr/bin/env python3
"""
Generate images using Gemini-API (Nano Banana).

Requirements:
  - pip install python-dotenv gemini_webapi Pillow
  - Create .env file with GEMINI_SECURE_1PSID=..., GEMINI_SECURE_1PSIDTS=... and GEMINI_SECURE_1PSIDCC=...
"""
import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from PIL import Image  # type: ignore
from gemini_webapi import GeminiClient, GeneratedImage


def play_alert():
    try:
        import subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alert_path = os.path.join(script_dir, "alert.mp3")
        if os.path.exists(alert_path):
            if sys.platform == "darwin":
                subprocess.run(["afplay", alert_path], check=False)
            elif sys.platform == "win32":
                os.startfile(alert_path)
            else:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", alert_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

async def generate_image(
    prompt: str,
    output_filename: str,
    retry_count: int = 3
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate an image using Gemini-API via subprocess and save it to disk.
    Returns tuple of (saved_path, error_message).
    """
    output_path = os.path.abspath(output_filename)
    output_dir = os.path.dirname(output_path) or '.'
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.basename(output_path)
    prefix = os.path.splitext(base_name)[0]
    
    script_path = os.path.abspath("tools/gemini_image_gen.py")
    
    for attempt in range(retry_count):
        try:
            cmd = [
                sys.executable,
                script_path,
                f"Generate {prompt} Aspect ratio: 16:9.",
                "-o", output_dir,
                "-p", prefix
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                generated_file = os.path.join(output_dir, f"{prefix}_0.png")
                
                if os.path.exists(generated_file):
                    if output_path.lower().endswith('.webp'):
                        try:
                            with Image.open(generated_file) as img_obj:
                                img_obj.save(output_path, "WEBP", quality=90)
                            os.remove(generated_file)
                        except Exception:
                            shutil.copy2(generated_file, output_path)
                            os.remove(generated_file)
                    else:
                        if generated_file != output_path:
                            shutil.copy2(generated_file, output_path)
                            os.remove(generated_file)
                    
                    return output_path, None
                else:
                    error = "Process succeeded but file not found."
                    if attempt < retry_count - 1:
                        await asyncio.sleep(5)
                        continue
                    return None, error
            else:
                error_msg = stdout.decode().strip() or stderr.decode().strip()
                if attempt < retry_count - 1:
                    await asyncio.sleep(5)
                    continue
                return None, f"Subprocess failed: {error_msg}"
                
        except Exception as e:
            if attempt < retry_count - 1:
                await asyncio.sleep(5)
            else:
                return None, f"Generation failed after {retry_count} attempts: {e}"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini-API (Nano Banana)."
    )
    parser.add_argument("prompt", nargs="?", default=None,
                        help="Text prompt describing the desired image (single mode)")
    parser.add_argument("output", nargs="?", default=None,
                        help="Output image filename (single mode)")
    parser.add_argument("--prompts", dest="prompts_file", default=None,
                        help="Path to prompts.json or directory for batch generation")
    parser.add_argument("--output-dir", dest="output_dir", default="images",
                        help="Directory to save images in batch mode (default: ./images)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing images if they already exist")
    parser.add_argument("--retry", dest="retry_count", type=int, default=3,
                        help="Number of retries if generation fails (default: 3)")
    return parser.parse_args()


async def process_batch(entries: list, images_dir: str, args: argparse.Namespace, 
                        current_file: str, log_file, error_log_file) -> list[Optional[str]]:
    saved = []
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            msg = f"Skipping invalid item at index {idx}: expected object"
            print(msg)
            log_file.write(msg + "\n")
            continue
        
        prompt_text = item.get("prompt")
        
        filename = item.get("filename")
        name = item.get("name")
        obj = item.get("object")
        
        target_name = filename or name or obj
        
        if not target_name or not prompt_text:
            msg = f"Skipping index {idx}: Missing 'filename'/'name'/'object' or 'prompt'"
            print(msg)
            log_file.write(msg + "\n")
            continue
            
        output_path = os.path.join(images_dir, target_name)
        
        if os.path.exists(output_path) and not args.overwrite:
            msg = f"  [{idx+1}/{len(entries)}] SKIPPED (exists): {target_name}"
            print(msg)
            log_file.write(msg + "\n")
            continue
        
        msg = f"  [{idx+1}/{len(entries)}] {current_file} -> {target_name}"
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()
        
        path, error = await generate_image(
            prompt_text,
            output_path,
            retry_count=args.retry_count,
        )
        
        if error:
            err_msg = f"ERROR: {target_name} - {error}"
            print(f"      -> {err_msg}")
            log_file.write(f"      -> {err_msg}\n")
            error_log_file.write(f"[{datetime.now().isoformat()}] {current_file}\n")
            error_log_file.write(f"  filename: {target_name}\n")
            error_log_file.write(f"  prompt: {prompt_text}\n")
            error_log_file.write(f"  error: {error}\n\n")
            error_log_file.flush()
            print(f"\n⛔ Dừng batch do gặp lỗi. Chạy lại lệnh để tiếp tục từ ảnh chưa tạo.")
            play_alert()
            sys.exit(1)
        else:
            print(f"      -> {path}")
            log_file.write(f"      -> {path}\n")
            saved.append(path)
        
        # Wait between generations to avoid rate limiting
        if idx < len(entries) - 1:
            import random
            wait_time = random.randint(5, 10)
            print(f"      Waiting {wait_time}s before next image...")
            await asyncio.sleep(wait_time)

    return saved


async def async_main() -> None:
    args = parse_args()
    
    secure_1psid = os.environ.get("GEMINI_SECURE_1PSID")
    
    if not secure_1psid:
        print("ERROR: GEMINI_SECURE_1PSID environment variable not set.", file=sys.stderr)
        print("Please add GEMINI_SECURE_1PSID, GEMINI_SECURE_1PSIDTS, and GEMINI_SECURE_1PSIDCC to your .env file.", file=sys.stderr)
        play_alert()
        sys.exit(1)

    # Batch mode
    if args.prompts_file:
        input_path = os.path.abspath(args.prompts_file)
        if not os.path.exists(input_path):
            print(f"prompts path not found: {input_path}", file=sys.stderr)
            play_alert()
            sys.exit(1)

        prompt_files = []
        if os.path.isdir(input_path):
            import glob
            prompt_files = sorted(glob.glob(os.path.join(input_path, "**/*.json"), recursive=True))
            if not prompt_files:
                print(f"No .json files found in directory: {input_path}", file=sys.stderr)
                play_alert()
                sys.exit(1)
            print(f"Found {len(prompt_files)} prompt files in {input_path}")
        else:
            prompt_files = [input_path]

        # Use provided output dir or default to ./images
        if os.path.isabs(args.output_dir):
            images_dir = args.output_dir
        else:
            images_dir = os.path.abspath(os.path.join(os.getcwd(), args.output_dir))
            
        os.makedirs(images_dir, exist_ok=True)
        print(f"Saving images to: {images_dir}")
        
        # Open log files
        log_path = os.path.join(images_dir, "_generation.log")
        error_log_path = os.path.join(images_dir, "_error.log")
        with open(log_path, "a", encoding="utf-8") as log_file, \
             open(error_log_path, "a", encoding="utf-8") as error_log_file:
            log_file.write(f"\n=== Run started at {datetime.now().isoformat()} ===\n")
            log_file.write(f"Model: Gemini API (Nano Banana), Size: Landscape 16:9\n")
            
            total_saved = 0
            for p_idx, p_file in enumerate(prompt_files):
                msg = f"--- Processing file {p_idx+1}/{len(prompt_files)}: {p_file} ---"
                print(msg)
                log_file.write(msg + "\n")
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                except Exception as read_err:
                    err_msg = f"Failed to read file {p_file}: {read_err}"
                    print(err_msg)
                    log_file.write(err_msg + "\n")
                    continue

                if not isinstance(entries, list):
                    err_msg = f"Skipping {p_file}: must contain a JSON array"
                    print(err_msg)
                    log_file.write(err_msg + "\n")
                    continue

                saved = await process_batch(entries, images_dir, args, p_file, log_file, error_log_file)
                total_saved += len(saved)
            
            final_msg = f"Finished processing. Total images generated: {total_saved}"
            print(final_msg)
            log_file.write(final_msg + "\n")
            print(f"Log saved to: {log_path}")
            print(f"Error log saved to: {error_log_path}")
        return

    # Single mode
    if not args.prompt or not args.output:
        print("Provide either: <prompt> <output> for single mode, or --prompts <file_or_dir> for batch mode", file=sys.stderr)
        play_alert()
        sys.exit(1)

    path, error = await generate_image(
        args.prompt,
        args.output,
        retry_count=args.retry_count,
    )
    
    if error:
        print(f"Error: {error}", file=sys.stderr)
        play_alert()
        sys.exit(1)
    else:
        print(path)


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
