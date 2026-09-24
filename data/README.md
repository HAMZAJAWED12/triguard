# data/ — what is tracked, what is not, and under which licence

Tracked here: hand-built sample inputs and synthetic media only. Real dataset
downloads and caches are gitignored (`data/hf_cache/`, `data/t2_samples/`,
`data/t3_samples/`, `data/t4_samples/`, `data/local_demo/`) and are never
committed. No dataset media (images, audio) is redistributed by this repo.

## Public datasets used by the evaluation tracks

| Track | Dataset (Hugging Face id) | Split / n | Licence | Attribution |
|---|---|---|---|---|
| T2 text | Civil Comments (`google/civil_comments`) | `test`, 500 rows, seed 42 | CC0-1.0 | Jigsaw / Conversation AI; Borkan et al. (2019) |
| T3 image-text | Memotion (`Ahren09/MMSoc_Memotion`) | `train`, 50 rows, seed 42 | research use (SemEval-2020 Task 8); meme images are third-party copyright — streamed, never committed | Sharma et al. (2020) |
| T4 speech | LibriSpeech (`openslr/librispeech_asr`, config `clean`) | `test`, 50 clips, seed 42 | CC BY 4.0 | Panayotov, Chen, Povey and Khudanpur (2015) |
| T4 events | ESC-50 (`ashraq/esc50`) | `train`, 50 clips, seed 42 | CC BY-NC 3.0 (academic, non-commercial) | Piczak (2015) |

Selection mechanism for every streamed dataset: seeded buffered shuffle over a
streaming iterator, first n non-empty rows kept — see
`src/triguard/data/datasets.py`, `image_datasets.py`, `audio_datasets.py`.
The committed evidence envelopes under `outputs/evaluation/` record the
dataset id, split, n and class balance per run; a few short failure-case
texts from Civil Comments (CC0) and Memotion OCR are quoted verbatim in those
envelopes for failure analysis.

Planned but not used: Hateful Memes (gated) and AudioSet (ships YouTube ids
only) — see Table E9 in `docs/report_evidence_tables.md` and DECISIONS.md
D-017 / D-018.

## Tracked sample media (all self-made, no third-party content)

| File | Origin |
|---|---|
| `sample_inputs/audio_test.wav` | espeak-ng text-to-speech |
| `sample_inputs/blip_test.png`, `sample_inputs/ocr_test.png` | generated with PIL |
| `sample_inputs/confounders/*.wav` | espeak-ng (see `scripts/make_confounder_media.py`) |
| `sample_inputs/triguard_eval_v1/manifest.json` | hand-built T6 set; provenance field inside |

Harmful *media* for the local demo lives in the gitignored `data/local_demo/`
folder (see `docs/ethics.md`). The short synthetic harmful *sentences* used as
test fixtures and T1/T6 items are tracked by design; they contain no slurs and
no real user content.
