---
name: data-vocab-step-5-generate-images
description: Use this skill when the user asks to batch-generate vocabulary images for a Unit. Trigger when the user references a Unit folder containing `vocab/image-prompts.json` and wants the corresponding `.webp` images produced under `lessons/media/<book>/<unit>/images/`, or when the user is following the lesson-data pipeline and is on "vocab step 5 generate images".
---

# Vocabulary Image Batch Generation

## Role

You are the operator of an existing batch-generation pipeline. Your job is to prepare the right command for the user to run, not to rewrite the generator.

## What this skill does

Given a Unit folder containing `vocab/image-prompts.json`, hand the user a one-line command that invokes [`scripts/generate_image.py`](scripts/generate_image.py). The script calls the Gemini API (Nano Banana model) via the `gemini_webapi` library, enforces a 16:9 landscape aspect ratio in the prompt instruction, converts the output to `.webp`, and writes one image per prompt into the Unit's media folder.

## When to use this skill

- The user explicitly asks to generate images for a Unit's vocabulary.
- The user provides a Unit folder path with `vocab/image-prompts.json` and expects the `.webp` images written under `lessons/media/<book>/<unit>/images/`.
- The user is following the lesson-data pipeline and is on "vocab step 5 generate images".

This skill does not generate the prompts — that is step 4. It also does not generate audio — that is step 6.

## Non-negotiable rules

A handful of rules cannot be relaxed because they protect either the dataset's integrity or the user's API quota:

- **Do not run the script yourself.** The script makes paid API calls and takes a long time per image; the user runs it in their own terminal so they can watch progress and abort if needed.
- **Do not rewrite or "improve" the script.** It is an existing, working pipeline. Any change should be a deliberate separate task, not a side effect of running it.
- The script is idempotent: it skips images that already exist unless `--overwrite` is passed. Do not bypass that behavior by deleting outputs.

## Prerequisites

Before producing the command, make sure the environment is ready:

1. **Python dependencies** installed: `python-dotenv`, `gemini_webapi`, `Pillow` (typically via `poetry install`).
2. **Gemini cookies** set in the project root `.env` — `GEMINI_SECURE_1PSID` and `GEMINI_SECURE_1PSIDTS`. Both come from `gemini.google.com` cookies (DevTools → Application → Cookies).

## Initial information needed

Ask the user for one thing, then derive the rest:

- **Target Directory** (`thư mục chứa file vocab/image-prompts.json`) — the exact path to the Unit directory holding `vocab/image-prompts.json`.

From that path, derive:

- **book_slug** — e.g. `gs9` for `global-success-9`.
- **unit_slug** — e.g. `unit-1`.

Wait for the user to provide the Target Directory. Do not guess.

## Workflow

### Step 1 — Verify inputs

1. Confirm `vocab/image-prompts.json` exists inside the Target Directory.
2. Confirm `.env` exists in the project root with `GEMINI_SECURE_1PSID` set.

### Step 2 — Produce the command for the user to run

Construct the command below and send it to the user verbatim. They run it themselves.

```bash
cd {PROJECT_ROOT} && poetry run python3 .agent/skills/skills-data-vocab-step-5-generate-images/scripts/generate_image.py \
  --prompts {TARGET_DIRECTORY}/vocab/image-prompts.json \
  --output-dir lessons/media/{book_slug}/{unit_slug}/images \
  --retry 3
```

Parameters:

| Parameter      | Value                                          | Description                                  |
| -------------- | ---------------------------------------------- | -------------------------------------------- |
| `--prompts`    | path to `image-prompts.json`                   | input prompt array                           |
| `--output-dir` | `lessons/media/{book_slug}/{unit_slug}/images` | where the `.webp` files are written          |
| `--retry`      | `3`                                            | retries per image on failure                 |
| `--overwrite`  | _(optional flag)_                              | regenerate images that already exist         |

What the user should know:

- The script enforces a **landscape 16:9 aspect ratio** via the prompt instruction.
- Existing images are **skipped** unless `--overwrite` is passed.
- There is a **30-second delay** between images to stay under API rate limits.
- The script writes `_generation.log` and `_error.log` into the output directory.

### Step 3 — After the run

Once the user reports completion:

1. Have them check `lessons/media/{book_slug}/{unit_slug}/images/_error.log` for failed generations.
2. If anything failed, they can re-run the same command — already-generated images are skipped, so only the missing ones retry.
