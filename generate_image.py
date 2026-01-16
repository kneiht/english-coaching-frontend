#!/usr/bin/env python3
"""
Generate images using ImageFX API (Imagen) via @rohitaryal/imagefx-api CLI.

Requirements:
  - npm i -g @rohitaryal/imagefx-api
  - pip install python-dotenv
  - Create .env file with GOOGLE_COOKIE=your_cookie
"""
import argparse

# Load .env file if exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env
import json
import os
import subprocess
import sys
import tempfile
import shutil
from typing import Optional
from PIL import Image  # type: ignore


def generate_image(prompt: str,
                   output_filename: str,
                   *,
                   model: str = "IMAGEN_3_5",
                   size: str = "LANDSCAPE",
                   retry_count: int = 3) -> tuple[Optional[str], Optional[str]]:
    """
    Generate an image using imagefx CLI and save it to disk.
    Returns tuple of (saved_path, error_message).
    
    Args:
        prompt: Text description of the image to generate
        output_filename: Target output path
        model: Model to use (IMAGEN_4, IMAGEN_3_5, etc.)
        size: Aspect ratio (LANDSCAPE, PORTRAIT, SQUARE)
        retry_count: Number of retries if generation fails
    """
    google_cookie = os.getenv("GOOGLE_COOKIE")
    if not google_cookie:
        return None, "GOOGLE_COOKIE environment variable not set. Get your cookie from labs.google and set: export GOOGLE_COOKIE='...'"
    
    # Create temp directory for imagefx output
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [
            "imagefx", "generate",
            "--prompt", prompt,
            "--model", model,
            "--size", size,
            "--count", "1",
            "--retry", str(retry_count),
            "--dir", temp_dir,
            "--cookie", google_cookie
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or f"Exit code {result.returncode}"
                return None, f"imagefx failed: {error_msg}"
            
            # Find the generated image in temp directory
            generated_files = [f for f in os.listdir(temp_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            
            if not generated_files:
                return None, "No image file found in output directory"
            
            source_path = os.path.join(temp_dir, generated_files[0])
            output_path = os.path.abspath(output_filename)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Convert to target format if needed
            if output_path.lower().endswith('.webp'):
                try:
                    image = Image.open(source_path)
                    image.save(output_path, "WEBP", quality=90)
                except Exception as e:
                    # Fallback to simple copy
                    shutil.copy2(source_path, output_path)
            else:
                shutil.copy2(source_path, output_path)
            
            return output_path, None
            
        except subprocess.TimeoutExpired:
            return None, "Generation timed out after 180 seconds"
        except FileNotFoundError:
            return None, "imagefx CLI not found. Install with: npm i -g @rohitaryal/imagefx-api"
        except Exception as e:
            return None, f"Unexpected error: {e}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images using ImageFX API (Imagen) via imagefx CLI."
    )
    parser.add_argument("prompt", nargs="?", default=None,
                        help="Text prompt describing the desired image (single mode)")
    parser.add_argument("output", nargs="?", default=None,
                        help="Output image filename (single mode)")
    parser.add_argument("--prompts", dest="prompts_file", default=None,
                        help="Path to prompts.json or directory for batch generation")
    parser.add_argument("--model", default="IMAGEN_3_5",
                        choices=["IMAGEN_3_5"],
                        help="Model to use for image generation (default: IMAGEN_3_5)")
    parser.add_argument("--size", default="LANDSCAPE",
                        choices=["LANDSCAPE", "PORTRAIT", "SQUARE"],
                        help="Aspect ratio of generated image (default: LANDSCAPE)")
    parser.add_argument("--output-dir", dest="output_dir", default="images",
                        help="Directory to save images in batch mode (default: ./images)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing images if they already exist")
    parser.add_argument("--retry", dest="retry_count", type=int, default=3,
                        help="Number of retries if generation fails (default: 3)")
    return parser.parse_args()


def process_batch(entries: list, images_dir: str, args: argparse.Namespace, 
                  current_file: str, log_file, error_log_file) -> list[Optional[str]]:
    """Process a batch of prompt entries."""
    saved = []
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            msg = f"Skipping invalid item at index {idx}: expected object"
            print(msg)
            log_file.write(msg + "\n")
            continue
        
        prompt_text = item.get("prompt")
        
        # Determine output filename: prioritize 'filename', then 'name', then 'object'
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
        
        # Skip if file already exists (unless overwrite is True)
        if os.path.exists(output_path) and not args.overwrite:
            msg = f"  [{idx+1}/{len(entries)}] SKIPPED (exists): {target_name}"
            print(msg)
            log_file.write(msg + "\n")
            continue
        
        msg = f"  [{idx+1}/{len(entries)}] {current_file} -> {target_name}"
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()
        
        path, error = generate_image(
            prompt_text,
            output_path,
            model=args.model,
            size=args.size,
            retry_count=args.retry_count,
        )
        
        if error:
            err_msg = f"ERROR: {target_name} - {error}"
            print(f"      -> {err_msg}")
            log_file.write(f"      -> {err_msg}\n")
            # Write to error log with prompt for reference
            from datetime import datetime
            error_log_file.write(f"[{datetime.now().isoformat()}] {current_file}\n")
            error_log_file.write(f"  filename: {target_name}\n")
            error_log_file.write(f"  prompt: {prompt_text}\n")
            error_log_file.write(f"  error: {error}\n\n")
            error_log_file.flush()
        else:
            print(f"      -> {path}")
            log_file.write(f"      -> {path}\n")
            saved.append(path)
            # Wait 30 seconds before next generation to avoid rate limiting
            if idx < len(entries) - 1:
                print("      Waiting 30s before next image...")
                import time
                time.sleep(30)

    return saved


def main() -> None:
    args = parse_args()

    # Batch mode
    if args.prompts_file:
        input_path = os.path.abspath(args.prompts_file)
        if not os.path.exists(input_path):
            raise SystemExit(f"prompts path not found: {input_path}")

        prompt_files = []
        if os.path.isdir(input_path):
            import glob
            # Find all json files in the directory recursively
            prompt_files = sorted(glob.glob(os.path.join(input_path, "**/*.json"), recursive=True))
            if not prompt_files:
                raise SystemExit(f"No .json files found in directory: {input_path}")
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
            from datetime import datetime
            log_file.write(f"\n=== Run started at {datetime.now().isoformat()} ===\n")
            log_file.write(f"Model: {args.model}, Size: {args.size}\n")
            
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

                saved = process_batch(entries, images_dir, args, p_file, log_file, error_log_file)
                total_saved += len(saved)
            
            final_msg = f"Finished processing. Total images generated: {total_saved}"
            print(final_msg)
            log_file.write(final_msg + "\n")
            print(f"Log saved to: {log_path}")
            print(f"Error log saved to: {error_log_path}")
        return

    # Single mode
    if not args.prompt or not args.output:
        raise SystemExit("Provide either: <prompt> <output> for single mode, or --prompts <file_or_dir> for batch mode")

    path, error = generate_image(
        args.prompt,
        args.output,
        model=args.model,
        size=args.size,
        retry_count=args.retry_count,
    )
    
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    else:
        print(path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
