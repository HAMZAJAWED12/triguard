# T2 sampling factsheet (facts only, with line pointers)

Scope: how the 500 Civil Comments rows behind the two T2 envelopes were
selected, what the envelopes record, and what they do not. No interpretation:
every line is a pointer to a tracked file, a committed envelope, a `git`
output or a script run. Where a "why" belongs it is marked `[STUDENT]`.

Line numbers are against git HEAD `908b1e5` (2026-09-24). Envelopes:
`outputs/evaluation/20260623-074102/t2/results.json` (sklearn tier, "074102")
and `outputs/evaluation/20260623-124802/t2/results.json` (toxic-bert tier,
"124802").

## 1. Source and split

| fact | value | pointer |
|---|---|---|
| Hub id / config / licence | `google/civil_comments`, config `None`, `CC0-1.0` | `src/triguard/data/datasets.py:77-82` (`_SOURCES`) |
| Split | `test` | CLI default `src/triguard/evaluation/run_t2.py:72-73`; envelopes `dataset.split` 074102:8, 124802:8 |
| Split size | "≈ 97k rows" | `docs/implementation_notes.md:28` (documentation statement; not re-verified offline in this session) |
| Fields used | `text`, `toxicity` | `datasets.py:80` (`text_field`), `datasets.py:100-107` |

## 2. Loading mechanics

| fact | value | pointer |
|---|---|---|
| Streaming load with `cache_dir` | `load_dataset(..., streaming=True, cache_dir=hf_cache)`; `hf_cache` defaults to `data/hf_cache/` | `datasets.py:189-197`; `datasets.py:49` |
| Seed | 42 | CLI default `run_t2.py:76-77`; loader default `datasets.py:145`; envelopes `config.seed` 074102:21, 124802:22 |
| Buffer constant | `_SHUFFLE_BUFFER = 10_000` | `datasets.py:56` |
| Buffer formula | `buffer_size = min(_SHUFFLE_BUFFER, max(sample_size * 20, 1000))` → for `sample_size=500`: `min(10000, max(10000, 1000)) = 10000` | `datasets.py:199` |
| Shuffle call | `ds.shuffle(seed=seed, buffer_size=buffer_size)` on an `IterableDataset` | `datasets.py:202` |
| Selection wording | seeded buffered shuffle over a streaming iterator, buffer 10,000; the 500 kept rows come from approximately the first 10,500 rows of the shard-shuffled stream, not a uniform draw over the whole split; shard count not verified offline | `datasets.py:199-218`; `docs/dataset_cards.md` A3 `selection.wording` |
| Row filter and cap | iterate; skip rows whose stripped `text` is empty; stop once 500 kept | `datasets.py:206-218` |
| Label rule (ground truth) | `1 if float(row["toxicity"]) >= 0.5 else 0` | `datasets.py:107` |
| Prediction rule | `pred_int = 1 if ev.toxicity_score >= args.threshold else 0`, threshold default 0.5 | `run_t2.py:113`; `run_t2.py:78-79`; envelopes `config.threshold` 074102:22, 124802:23 |
| Sample cache file name | `{source}_{config or "default"}_{split}_n{sample_size}_seed{seed}.json` → `data/t2_samples/civil_comments_default_test_n500_seed42.json` | `datasets.py:112-116` |
| Sample cache written | `_write_cache` after streaming | `datasets.py:132-137` |
| Cache gitignored | `data/t2_samples/` | `.gitignore:32` |
| Cache present in this checkout | no (`ls data/` has no `t2_samples/`) | shell `ls data/`, 2026-09-24 |
| Cache row schema | `text`, `label`, `source` only — no dataset row id | `datasets.py:59-69` (`LabeledTextSample`) |
| Dataset revision | not pinned; re-stream on a fresh clone "is *not* guaranteed identical" | `datasets.py:26-29` |

## 3. What the two envelopes record

| fact | 074102 (sklearn) | 124802 (hf) | pointer |
|---|---|---|---|
| `n_samples` | 500 | 500 | 074102:10, 124802:10 |
| `class_balance` | `{"non-toxic": 468, "toxic": 32}` | `{"non-toxic": 468, "toxic": 32}` | 074102:15-18, 124802:15-18 |
| `config.sample_size` / `seed` / `threshold` | 500 / 42 / 0.5 | 500 / 42 / 0.5 | 074102:20-22, 124802:21-23 |
| `config.backend` | key absent | `hf` | 074102:19-24 (keys: `sample_size`, `seed`, `threshold`, `wrapper_mode` only), 124802:20 |
| `config.wrapper_mode` | `real` | `real-hf` | 074102:23, 124802:24 |
| `config.run_env` | key absent | `wsl-ubuntu` | 074102:19-24, 124802:25 |
| `model_versions.text_model` | `sklearn-tfidf-lr` | `unitary/toxic-bert` | 074102:26, 124802:28 |
| `model_versions.text_model_revision` | key absent | `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` | 124802:29 |
| `run_at` | `2026-06-23T07:41:02` | `2026-06-23T12:48:02` | 074102:3, 124802:3 |

Two bare facts, no inference drawn here:

- The `class_balance` object is identical in both envelopes (074102:15-18 and 124802:15-18).
- The same failure text appears in both `failures` lists: the entry beginning `"Yet, more potty talk…"` is at 074102:66 (score 0.4216) and at 124802:63 (score 0.0158).

Derived (not in the envelopes; produced by `scripts/ci_from_envelope.py --write` from the committed confusion matrices):

| metric | 074102 k/n → point [Wilson 95%] | 124802 k/n → point [Wilson 95%] | file |
|---|---|---|---|
| accuracy | 271/500 → 0.542 [0.4982, 0.5852] | 464/500 → 0.928 [0.9019, 0.9475] | `outputs/evaluation/<run>/t2/derived_intervals.json` `values.accuracy` |
| toxic precision | 19/235 → 0.0809 [0.0524, 0.1228] | 9/22 → 0.4091 [0.2326, 0.6127] | `values.toxic_precision` |
| toxic recall | 19/32 → 0.5938 [0.4226, 0.7448] | 9/32 → 0.2812 [0.1556, 0.4537] | `values.toxic_recall` |

The `point` values equal the envelopes' own `accuracy` / `per_class.toxic.precision` / `per_class.toxic.recall` (copied into each derived file under `point_estimates_in_envelope`).

## 4. NOT recorded anywhere in the repo

| item | what exists instead |
|---|---|
| Reason for `sample_size=500` | only the CLI default (`run_t2.py:74`), the protocol wording "Reproducible, capped sample (default 500 rows, seed 42)" (`docs/evaluation_protocol.md:35`) and the D-011 Reason sentence (`DECISIONS.md:118-120`) |
| T2 wall time | no key in either envelope |
| Hardware (CPU/GPU/RAM) for the T2 runs | no key in either envelope; 124802 has only `run_env: "wsl-ubuntu"` |
| Dataset revision hash | none (`datasets.py:26-29`) |
| Dataset row ids of the 500 rows | not stored in the cache schema (`datasets.py:59-69`) nor in the envelopes |
| Full-split positive rate (toxicity ≥ 0.5 over the whole `test` split) | never computed; only the 32/500 sample count exists |
| `run_env` / `backend` for the sklearn run | keys absent (074102:19-24) |

## 5. Sampling frame per streamed track

"Rows consumed ≈ buffer + n" because a buffered shuffle first fills the buffer, then each yielded row is replaced by the next streamed row; filters skip rows after they are drawn, so the true count can only be higher.

| track | loader | buffer constant (line) | shuffle call (line) | cap (default) | filter | rows consumed ≈ |
|---|---|---|---|---|---|---|
| T2 | `src/triguard/data/datasets.py` | 10,000 (`:56`, formula `:199`) | `:202` | 500 (`run_t2.py:74`) | non-empty text | ~10,500 |
| T3 | `src/triguard/data/image_datasets.py` | 2,000 (`:37`) | `:117` | 50 (`run_t3.py:43`) | label parseable + image decodable | ~2,050 |
| T4 LibriSpeech | `src/triguard/data/audio_datasets.py` | 2,000 (`:38`) | `:180` | 50 (`run_t4.py:54`) | non-empty reference + audio array | ~2,050 |
| T4 ESC-50 | `src/triguard/data/audio_datasets.py` | 2,000 (`:38`) | `:224` | 50 (`run_t4.py:54`) | category in `ESC50_TO_YAMNET` (42 of 50 categories, `:65-108`) + audio array | ≥ ~2,050 (unmapped categories skipped; count not recorded) |

Cache-vs-envelope check (run 2026-09-24, `scripts/build_dataset_cards.py --cache-root …`, path not recorded): T2 cache 500 rows, 468/32 = envelope; T3 cache 50 rows, 18/32 = envelope; T4 caches 50 + 50 rows, ESC-50 29 distinct categories = envelope `categories_used`. See `docs/dataset_cards.md` header.

## For integration

### Table E3a — T2 sampling & run parameters (Ch5.3)

| row | 074102 (sklearn tier) | 124802 (toxic-bert tier) | source |
|---|---|---|---|
| hub_id | `google/civil_comments` | `google/civil_comments` | `dataset.hub_id` (074102:6, 124802:6) |
| split | `test` | `test` | `dataset.split` (074102:8, 124802:8) |
| label rule | `toxicity >= 0.5 → toxic` | same | `datasets.py:107` |
| sampling | seeded buffered shuffle, seed 42, buffer 10,000, first 500 non-empty rows (~10,500 rows of the shard-shuffled stream; not a uniform draw over the split) | same | `datasets.py:56,199,202,206-218` |
| n | 500 | 500 | `n_samples` |
| class_balance | 468 non-toxic / 32 toxic | 468 / 32 | `class_balance` (074102:15-18, 124802:15-18) |
| threshold | 0.5 | 0.5 | `config.threshold` |
| backend / wrapper_mode | backend key absent / `real` | `hf` / `real-hf` | `config` (074102:19-24, 124802:20-24) |
| model_revision | n/a (`sklearn-tfidf-lr`, trained in-process on the 30-sentence corpus) | `4d6c22e74ba2fdd26bc4f7238f50766b045a0d94` | `model_versions` (074102:26, 124802:28-29) |
| run_env | not recorded | `wsl-ubuntu` | `config.run_env` (124802:25) |
| dataset revision | unpinned | unpinned | `datasets.py:26-29` |
| run id | `20260623-074102` | `20260623-124802` | directory names |
| Wilson 95% CI (derived) | acc [0.4982, 0.5852]; toxic P [0.0524, 0.1228]; toxic R [0.4226, 0.7448] | acc [0.9019, 0.9475]; toxic P [0.2326, 0.6127]; toxic R [0.1556, 0.4537] | `derived_intervals.json` next to each envelope |

### DECISIONS.md draft entry (for the Integrate stage to place; number to confirm)

```
## Decision 032: Derived statistics from committed envelopes (numbered by DECISIONS.md; drafted here as 031)
Date: 2026-09-24
Status: proposed

Context: The committed T2 envelopes carry point estimates and confusion
matrices but no interval estimates. `scripts/ci_from_envelope.py` (new,
stdlib `math` only) reads a committed `results.json` confusion matrix and,
with `--write`, stores `derived_intervals.json` beside it recording
`derived_from`, `method` ("Wilson score interval, z=1.959964"), the copied
matrix, k/n per metric and the interval bounds. Files produced:
`outputs/evaluation/20260623-074102/t2/derived_intervals.json`,
`outputs/evaluation/20260623-124802/t2/derived_intervals.json`. The
envelopes themselves are untouched. Unit test:
`tests/test_ci_from_envelope.py` (hand-worked expected values).
Options considered: [STUDENT]
Decision: [STUDENT] — candidate wording: "Derived statistics from committed
envelopes are citeable when produced by a committed script into a
`derived_*.json` next to the envelope."
Reason: [STUDENT]
Impact: two new derived files under `outputs/evaluation/` (inputs
read-only); one new script; one new test (+2 tests in the fast lane);
`docs/t2_sampling_factsheet.md` and `docs/dataset_cards.md` reference the
derived values with their file path and key.
```

## [STUDENT] — reasons the repo does not state (facts available to draw on)

- **Why 500 rows for T2.** The repo holds no stated reason. Available facts: CLI default `run_t2.py:74`; protocol wording `docs/evaluation_protocol.md:35` ("Reproducible, capped sample (default 500 rows, seed 42)"); D-011 Reason (`DECISIONS.md:118-120`: "streaming + a fixed seed + a cached sample keep it small, reproducible and offline-after-first-run"); the buffer formula means 500 is the smallest cap that reaches the full 10,000 buffer (`datasets.py:199`: `500 * 20 = 10000`); resulting positive-class count 32 and its Wilson CI widths (section 3, derived table).
- **Why 50 for T3 / T4.** No stated reason. Available facts: CLI defaults `run_t3.py:43`, `run_t4.py:54`; D-018 (`DECISIONS.md:345`: "Stream (seed 42, cap 50)"); D-017 (`DECISIONS.md:326`: "seed 42, n=50 each"); protocol planned 200 AudioSet clips (`docs/evaluation_protocol.md:50`); Table E9 rows T3/T4 (`docs/report_evidence_tables.md:285-286`); envelope limitation strings "small sample (<= 50); indicative, not a benchmark claim" (T3) and "small samples (<= 50 clips each)" (T4); Memotion media are third-party copyright and persisted to a gitignored cache (`image_datasets.py:12-15`).
- **Why 24 items for T6.** No stated reason. Available facts: protocol planned a 50-item set (`docs/evaluation_protocol.md:63`); v1 had 18 AI-drafted items (`git show c8f22a8:…manifest.json`, card A7); v2 has 24 student-reviewed items 10/6/8 (D-026, `DECISIONS.md:641-643`; card A8); Table E9 T6 row gives "authoring capacity; provenance honesty (D-022, D-026)" (`docs/report_evidence_tables.md:289`); the confounder template holds 12 unfilled slots (card A9).
