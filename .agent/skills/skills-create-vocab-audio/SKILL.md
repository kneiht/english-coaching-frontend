---
name: create-vocab-audio
description: Batch-generate vocabulary and sentence audio files from lesson-*-vocab.json files in a unit folder, saving output directly inside the unit folder.
---

# Create Vocabulary Audio Skill

This skill batch-generates audio files for all vocabulary words and example sentences defined in JSON files within a target unit directory.

## Usage

Run the Python helper script with the path to the target directory containing your `lesson-*-vocab.json` files:

```bash
python3 .agent/skills/skills-create-vocab-audio/scripts/create_audio.py <path_to_unit_dir>
```

**Example:**

```bash
python3 .agent/skills/skills-create-vocab-audio/scripts/create_audio.py src/mock-data/lessons/advanced-topics/the-psychology-of-color
```

## How It Works

1. Scans the target folder for all files matching `lesson-*-vocab.json`.
2. Extracts all vocabulary objects containing `word`, `sampleSentence`, `wordPronunciation`, and `sentencePronunciation`.
3. Invokes the project-root `tts_gemini.py` script to generate pronunciation audios via Gemini TTS.
4. Saves word audio files into `<path_to_unit_dir>/audio-words/`.
5. Saves sentence audio files into `<path_to_unit_dir>/audio-sentences/`.
