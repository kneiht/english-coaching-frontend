---
name: create-vocab-images
description: Batch-generate vocabulary images (.webp) from lesson-*-vocab.json files in a unit folder using Gemini API, saving output directly inside the unit folder.
---

# Create Vocabulary Images Skill

This skill uses the Gemini API to automatically generate descriptive visual prompts and then create `.webp` images for all vocabulary words in a target unit directory.

## Usage

Run the Python helper script with the path to the target directory containing your `lesson-*-vocab.json` files:

```bash
python3 .agent/skills/skills-create-vocab-images/scripts/create_images.py <path_to_unit_dir>
```

**Example:**

```bash
python3 .agent/skills/skills-create-vocab-images/scripts/create_images.py src/mock-data/lessons/advanced-topics/the-psychology-of-color
```

## How It Works

1. Scans the target folder for all files matching `lesson-*-vocab.json`.
2. Extracts all vocabulary words and meanings.
3. Calls the Gemini API to generate detailed photorealistic visual prompts for each word.
4. Invokes the batch image generator to create and save the `.webp` files into `<path_to_unit_dir>/images-words/`.
5. Already-existing files in the output directory are skipped to save API limits.
