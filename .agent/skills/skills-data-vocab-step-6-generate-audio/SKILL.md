---
name: data-vocab-step-6-generate-audio
description: Use this skill when the user asks to batch-generate vocabulary audio for a Unit. Trigger when the user references a Unit folder containing `vocab/vocab.json` and wants per-word and per-sentence `.mp3` files produced under `lessons/media/<book>/<unit>/audio/` via Gemini TTS, or when the user is following the lesson-data pipeline and is on "vocab step 6 generate audio".
---

# Vocabulary Audio Batch Generation

## Role

You are the operator of an existing batch-generation pipeline. Your job is to prepare the right command for the user to run, not to rewrite the generator.

## What this skill does

Given a Unit folder containing `vocab/vocab.json`, hand the user a one-line command that invokes [`scripts/generate_vocab_audio.py`](scripts/generate_vocab_audio.py). The script uses Gemini 2.5 Flash TTS to produce two `.mp3` files per vocabulary word:

- `audio/{word}.mp3` — clear, neutral reading of the English word.
- `audio/{word}-sentence.mp3` — clear, neutral reading of the word's example sentence.

The voice is `Kore` (firm, clear) and director notes enforce a flat, neutral delivery — no acting, whispering, or emotion. This keeps the listening experience consistent across the dataset.

## When to use this skill

- The user explicitly asks to generate vocabulary audio for a Unit.
- The user provides a Unit folder path with `vocab/vocab.json` and expects `.mp3` files under `lessons/media/<book>/<unit>/audio/`.
- The user is following the lesson-data pipeline and is on "vocab step 6 generate audio".

This skill does not generate images — that is step 5. It also does not generate audio for other materials (reading passages, listening tracks) — each has its own skill.

## Non-negotiable rules

A handful of rules cannot be relaxed because they protect either the dataset's consistency or the user's API quota:

- **Do not run the script yourself.** The script makes paid API calls (two per word) and takes a long time; the user runs it in their own terminal so they can watch progress and abort if needed.
- **Do not rewrite or "improve" the script.** It is an existing, working pipeline.
- The director notes inside the script are intentionally **neutral and flat**. Do not edit them to add emotion, character, or "expressiveness" — the dataset depends on a uniform delivery style.
- The script is idempotent: it skips files that already exist unless `--overwrite` is passed. Do not bypass that behavior by deleting outputs.

## Prerequisites

Before producing the command, make sure the environment is ready:

1. **Python dependencies** installed: `google-genai`, `python-dotenv`, `pydub` (typically via `poetry install`).
2. **ffmpeg** installed for WAV → MP3 conversion (`brew install ffmpeg` on macOS).
3. **Google API key** set in the project root `.env` — `GOOGLE_API_KEY`.

## Initial information needed

Ask the user for one thing, then derive the rest:

- **Target Directory** (`thư mục chứa file vocab/vocab.json`) — the exact path to the Unit directory holding `vocab/vocab.json`.

From that path, derive:

- **book_slug** — e.g. `gs9` for `global-success-9`.
- **unit_slug** — e.g. `unit-1`.

Wait for the user to provide the Target Directory. Do not guess.

## Workflow

### Step 1 — Verify inputs

1. Confirm `vocab/vocab.json` exists inside the Target Directory.
2. Confirm `.env` exists in the project root with `GOOGLE_API_KEY` set.

### Step 2 — Produce the command for the user to run

Construct the command below and send it to the user verbatim. They run it themselves.

```bash
cd {PROJECT_ROOT} && poetry run python3 .agent/skills/skills-data-vocab-step-6-generate-audio/scripts/generate_vocab_audio.py \
  {TARGET_DIRECTORY}/vocab/vocab.json \
  --output-dir lessons/media/{book_slug}/{unit_slug}/audio \
  --delay 5
```

Parameters:

| Parameter         | Value                                         | Description                                |
| ----------------- | --------------------------------------------- | ------------------------------------------ |
| `vocab.json`      | path to vocab file                            | input vocabulary data                      |
| `--output-dir`    | `lessons/media/{book_slug}/{unit_slug}/audio` | where the `.mp3` files are written         |
| `--delay`         | `5`                                           | seconds between API calls (rate limiting)  |
| `--overwrite`     | _(optional flag)_                             | regenerate files that already exist        |
| `--word-only`     | _(optional flag)_                             | generate only the word audio               |
| `--sentence-only` | _(optional flag)_                             | generate only the sentence audio           |

What the user should know:

- Each word produces **two API calls** (word + sentence).
- Voice: `Kore` (firm, clear); delivery is neutral and flat by design.
- Existing files are **skipped** unless `--overwrite` is passed.

### Step 3 — After the run

Once the user reports completion:

1. Have them check `lessons/media/{book_slug}/{unit_slug}/audio/_error.log` for failures.
2. If anything failed, they can re-run the same command — already-generated files are skipped, so only the missing ones retry.
