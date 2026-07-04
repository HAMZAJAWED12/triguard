# TriGuard T6 evaluation set (triguard_eval_v1)

Hand-built tri-modal set for evaluation track **T6** and the cross-modal ablation.
**You author the items.** The confounder cases and their ground-truth labels are
your own intellectual work; this README only documents the format the harness reads.

## File

`manifest.json` — `{ "schema_version": "1", "items": [ ... ] }`.

## Item fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique id, e.g. `S1` (safe), `H2` (harmful), `X1` (cross-modal). |
| `label` | `"safe"` \| `"borderline"` \| `"harmful"` | **Ground truth** — your holistic judgement of the item *as a whole* (all modalities together). |
| `cross_modal` | boolean | `true` if the harm/risk emerges only from the **combination** (each modality alone is benign). This flag selects the items the ablation reports on. |
| `text` | string \| null | The text content, or `null` if the item has no text. |
| `image` | string \| null | Path to an image file (see paths below), or `null`. |
| `audio` | string \| null | Path to an audio file, or `null`. |
| `unimodal_labels` | object \| omit | Optional. Your judgement of what **each modality alone** should read as: `{ "text": <label|null>, "image": <label|null>, "audio": <label|null> }`. For a confounder these are each `safe` while `label` is `harmful`. Used to characterise the ablation. |
| `notes` | string \| omit | Optional. Why the case exists (kept out of metrics). |

At least one of `text` / `image` / `audio` must be non-null per item.

## Paths

`image` / `audio` paths resolve from the **repo root** (the harness runs from
`/mnt/c/dev/triguard`), e.g. `data/sample_inputs/triguard_eval_v1/media/x1.png`.
Put media under a `media/` subfolder here.

## Media + licensing

- Commit only **small, benign, public-domain / self-made** media. Reuse the existing
  `data/sample_inputs/blip_test.png` and `audio_test.wav` where they fit.
- Do **not** commit copyrighted media (memes, others' photos/clips). If a case needs
  such media, gitignore it and document the source in `notes`.
- No harmful media is committed to the repo (ethics rule).

## Suggested balance (your call)

~30–50 items, roughly balanced across `safe` / `borderline` / `harmful`, with a
meaningful subset marked `cross_modal: true` — those are what prove the thesis
(multimodal catches what unimodal misses).

## What the harness will do (Phase A, run_t6.py)

For every item it runs the pipeline in four conditions — text-only, image-only,
audio-only, full-multimodal — and compares each prediction to your `label`. The
headline is multimodal recall on the `cross_modal: true` harmful items versus the
best single modality.
