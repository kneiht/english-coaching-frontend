#!/usr/bin/env python3
"""
Convert MP3 files to WAV and organize into words/sentences folders.
"""
import os
import subprocess
import sys

def convert_and_organize(audio_dir: str):
    """Convert MP3 to WAV and organize into audio-words and audio-sentences."""
    
    # Create output directories
    words_dir = os.path.join(os.path.dirname(audio_dir), "audio-words")
    sentences_dir = os.path.join(os.path.dirname(audio_dir), "audio-sentences")
    os.makedirs(words_dir, exist_ok=True)
    os.makedirs(sentences_dir, exist_ok=True)
    
    # Get all MP3 files
    mp3_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
    print(f"Found {len(mp3_files)} MP3 files")
    
    words_count = 0
    sentences_count = 0
    
    for idx, mp3_file in enumerate(sorted(mp3_files)):
        name = mp3_file[:-4]  # Remove .mp3
        input_path = os.path.join(audio_dir, mp3_file)
        
        # Count words in filename (split by hyphen)
        word_count = len(name.split('-'))
        
        # Short names (1-3 words) = word pronunciation
        # Long names (4+ words) = sentence pronunciation
        if word_count <= 3:
            output_path = os.path.join(words_dir, f"{name}.wav")
            folder_type = "word"
            words_count += 1
        else:
            output_path = os.path.join(sentences_dir, f"{name}.wav")
            folder_type = "sentence"
            sentences_count += 1
        
        print(f"[{idx+1}/{len(mp3_files)}] {mp3_file} -> {folder_type}")
        
        # Convert using ffmpeg
        try:
            subprocess.run(
                ['ffmpeg', '-i', input_path, '-y', output_path],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: {e}")
            continue
    
    print("-" * 50)
    print(f"Words: {words_count} files in {words_dir}")
    print(f"Sentences: {sentences_count} files in {sentences_dir}")
    print("Done!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        audio_path = "src/mock-data/lessons/advanced-topics/light-pollution/audio"
    
    convert_and_organize(audio_path)
