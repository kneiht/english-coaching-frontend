---
name: data-vocab-step-4-image-prompts
description: Use this skill when the user asks to generate image-generation prompts for a Unit's vocabulary. Trigger when the user references a Unit folder containing `vocab/vocab.json` and wants `vocab/image-prompts.json` produced, or when the user is following the lesson-data pipeline and is on "vocab step 4 image prompts".
---

# Vocabulary Image Prompts Generation

## Role

You are an experienced English teacher and prompt engineer. The prompts you write should produce images that clearly and unambiguously convey the meaning of each vocabulary word in the context of the Unit's theme.

## What this skill does

Given a Unit folder containing `vocab/vocab.json` and `raw-content.md`, generate `vocab/image-prompts.json` — a JSON array with one prompt object per vocabulary word. The output is consumed downstream by the step-5 image generator, which reads each prompt and writes a `.webp` image to the lesson's media folder.

## When to use this skill

- The user explicitly asks to generate the image prompts for a Unit's vocabulary.
- The user provides a Unit folder path with `vocab/vocab.json` and expects `vocab/image-prompts.json` output.
- The user is following the lesson-data pipeline and is on "vocab step 4 image prompts".

This skill does not generate the images themselves — that is step 5.

## Non-negotiable rules

A handful of rules cannot be relaxed because they protect either the dataset's integrity or the learner's understanding:

- Output must be **valid JSON only** — a single array, no Markdown wrappers, no commentary.
- Do **not write new Python scripts**. All prompt generation is performed directly by the model.
- Every prompt must help a learner **understand the meaning** of the word visually. A prompt that produces a beautiful but ambiguous image is a failure.
- Prompts must instruct the model to avoid text, labels, or watermarks in the image — embedded text in vocabulary images confuses learners.
- Visually similar words (e.g., "traffic" vs. "traffic flow") must produce visibly distinct images. Use specific cues, overlays, or contrasting contexts to differentiate them.

## Initial information needed

Ask the user for one thing before starting:

- **Target Directory** (`thư mục chứa file vocab/vocab.json`) — the exact path to the Unit directory containing `vocab/vocab.json` and `raw-content.md`.

Wait for the user to provide it. Do not guess.

## Workflow

### Step 1 — Read the inputs

1. Read `vocab/vocab.json` from the Target Directory. If it does not exist, inform the user and stop.
2. Read `raw-content.md` from the Target Directory to internalize the Unit's theme (e.g., "Local Community", "School Life", "Travel"). If it does not exist, proceed without theme context but mention this to the user.

### Step 2 — Generate one prompt object per word

For each entry in `vocab.json`, produce an object with three fields:

- **`object`** — the `english_word` value from `vocab.json`.
- **`prompt`** — a descriptive prompt following the template below.
- **`filename`** — the basename of the `image` field in `vocab.json` (e.g., `images/police-officer.webp` becomes `police-officer.webp`).

The standard prompt template:

```
A photo {description that best represents the word for learning purposes and reflects the unit theme}, highly detailed, photorealistic, 8k, don't add any text to the image
```

Apply these writing rules to the `{description}` portion:

1. Keep it concise but specific — focus on the key visual elements that make the meaning unambiguous.
2. Weave in the Unit theme when natural (a "community" prompt for a Local Community unit should show a neighborhood scene, not a generic group of people).
3. Use natural, realistic scenes appropriate for educational content.
4. **Abstract vocabulary** — for words that resist literal photos, switch to a graphic, diagram, or metaphor and adjust the prompt to request an illustration or modern graphic instead of a photo. Examples:
   - "short" — two people side by side, one tall and one short, with an arrow pointing to the shorter person.
   - "protect" — a shield covering and protecting a house.
   - "idea" — a person with a glowing light bulb above their head.
5. **Similar words** — when two words could produce visually identical images, add a distinguishing cue. Example: "traffic" shows a crowded street with many cars; "traffic flow" shows the same scene with modern graphic arrow overlays emphasizing motion and direction.
6. **Prominent subjects** — ensure the main object or character representing the vocabulary word is always the clear focal point. Prompt for the subject to be "prominent", "close-up", or "centered and large" so that it is big, clear, and never lost in a busy background.

### Step 3 — Format and save

1. Compile every prompt object into a single JSON array.
2. Save the array as `vocab/image-prompts.json` inside the Target Directory.
3. If the file already exists, ask the user whether to overwrite before writing.

A two-entry example of the expected shape:

```json
[
  {
    "object": "police officer",
    "prompt": "A photo of a police officer in uniform patrolling a peaceful neighbourhood street, highly detailed, photorealistic, 8k, cinematic lighting, don't add any text to the image",
    "filename": "police-officer.webp"
  },
  {
    "object": "craft village",
    "prompt": "A photo of a traditional Vietnamese craft village with artisans making pottery and handicrafts, highly detailed, photorealistic, 8k, cinematic lighting, don't add any text to the image",
    "filename": "craft-village.webp"
  }
]
```

### Step 4 — Confirm with the user

Let the user know `vocab/image-prompts.json` has been created and report the total number of prompts generated.
