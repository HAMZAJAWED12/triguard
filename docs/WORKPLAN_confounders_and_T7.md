# Work plan — confounder set, T6 stability, T7 ratings

Everything left before the final report's evidence is complete. Keep this
file open while you work. Commands are copy-paste; run them from PowerShell
unless a block says WSL shell.

Time estimate: confounder set ~3–4 h (mostly design + photos), T6 stability
~10 min of waiting, T7 ratings ~20 min.

---

## TASK 1 — design 12 confounder cases (paper first, no code)

This is the assessed intellectual contribution: the design, the wording, the
media choice and every label are yours. The rest of this file is mechanics.

### What you are building

A confounder = **each modality benign alone, the combination harmful.** If
either part is already harmful by itself, it is not a confounder — the v2 set
already covers that case, and adding more proves nothing new.

### How the literature builds them (for your method section)

Kiela et al. (2020) construct the Hateful Memes benchmark by taking a
multimodal example and swapping ONE modality for a "benign confounder" that
flips the label. Because both the hateful and the benign version share one
half, a model that only reads text, or only reads images, cannot beat chance
on the pairs — meaning lives in the combination. Human accuracy on the set is
about 85%; image-only baselines sit near chance (~52%) and the strongest
text-only baseline reaches only ~59%. Your set is a miniature of the same
idea, scaled to what a single student can author and label honestly.

### The four questions — answer in writing for every case

1. **Text**: what is it, and is it genuinely safe standing alone? Would you
   flag it if you saw only that sentence? If yes → not a confounder.
2. **Media**: what is the image or audio, and is it genuinely safe alone?
3. **Combination**: what does the pair mean that neither part means? One
   sentence. This becomes `design_note` and later your method prose.
4. **Pattern**: which of the four?
   - P1 text recontextualises image
   - P2 image gives a target to generic text
   - P3 instruction + object
   - P4 spoken words recontextualise text/image

### Rules that make a case valid (the validator enforces all of these)

- `label` = `harmful` or `borderline` (the combination), and you can defend
  that label to an examiner. **Prefer `harmful`**: the headline thesis metric
  (`recall_by_condition`) counts only harmful confounders caught as
  `harmful`. Borderline confounders are scored in a separate
  `borderline_recall_by_condition` block, so nothing you author is lost, but
  they do not move the headline number. Label honestly — do not inflate a
  case to `harmful` to feed the metric; a defensible borderline is worth more
  than an indefensible harmful.
- Every supplied modality's `unimodal_labels` = `safe`.
- At least 2 modalities present.
- Harm comes from **meaning**, never from shocking media.
- Media is benign, self-made or public domain, committable.

### Audio rail (important, learned the hard way)

"Tone of voice" cannot work in this system. espeak output is monotone,
YAMNet tags acoustic events not delivery, and Whisper keeps only the words —
**prosody never reaches the judge**. An audio confounder must carry its
recontextualisation in the transcript WORDING (P4), or hinge on a
YAMNet-taggable event. Design most cases on P1–P3.

### Image rail (the same trap, image side)

OCR is **off** during T6 runs and **on** in the demo server. So words written
inside a photo (a sign, a label, a screen) do not reach the judge in the
evaluation, even though the same image behaves differently at `/ui`. The
BLIP pre-flight will not warn you — it happily captions "a sign on a pole"
while the words on the sign vanish.

**Design the harm as an OBJECT or SCENE the caption can name, never as text
inside the picture.** (Do not "fix" this by adding `TRIGUARD_IMAGE_OCR=1` to
the T6 commands: the committed baselines were run OCR-off, and turning it on
would make your new numbers incomparable with them.)

### Suggested spread across 12 slots

Balance rather than repeating one trick — e.g. 4× P1, 3× P2, 3× P3, 2× P4.
Adjust to what you can actually photograph.

### Common failure modes — check yours against these

| failure | why it kills the case |
|---|---|
| one part already harmful | not a confounder; measures nothing new |
| harm depends on visual detail a caption drops | BLIP flattens it before any judge sees it (Task 3 catches this) |
| harm depends on tone of voice | prosody never reaches the judge |
| label you cannot defend | an examiner will ask "why harmful?" — you must answer |
| media that is disturbing alone | breaks the ethics rails and the confounder property at once |

---

## TASK 2 — produce media

Everything lands in `data/sample_inputs/confounders/`.

### TTS clips (available now, no equipment)

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/make_confounder_media.py --tts 'the exact words spoken in the clip' --out cf4_words.wav"
```

espeak writes 22.05 kHz mono; the audio wrapper resamples to its own 16 kHz.
Name files `cf<N>_<short-slug>.wav` so the manifest stays readable.

**Apostrophes break the command** — the spoken text sits inside bash single
quotes, so `don't` ends the quote early (`unexpected EOF while looking for
matching '''`). Two options: avoid contractions in the wording, or escape
each apostrophe as `'\''`:

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/make_confounder_media.py --tts 'don'\''t stand there' --out cf4_words.wav"
```

Same for double quotes inside the sentence — leave them out.

### Photos

Shoot everyday objects/scenes on your phone: a tool, a doorway, a vehicle, a
building, a sign. **No faces, no identifiable people or places.** Transfer to
your Pictures folder (on many Windows machines it is OneDrive-redirected —
check where the photos actually land before typing paths).

List what actually arrived, so you use real filenames:

```bash
wsl -e bash -lc "ls -1 '/mnt/c/Users/<you>/Pictures/'"
```

Import each one (resizes to ≤1024 px long edge, converts to PNG, strips
EXIF/GPS):

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/make_confounder_media.py --import '/mnt/c/Users/<you>/Pictures/<photo>.jpg' --out cf1_object.png"
```

Replace the source path with your real filename. Single-quote paths — several
folders have spaces.

### Public-domain alternative

Wikimedia Commons filtered to public domain / CC0. Record source URL +
licence per image; the report needs that line. Weaker than own photos for
the originality criterion.

---

## TASK 3 — BLIP pre-flight every image

Before an image earns a slot, check the harm-carrying object survives BLIP's
one-line caption. If it does not, no judge downstream can ever see it.

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python scripts/make_confounder_media.py --caption data/sample_inputs/confounders/cf1_object.png"
```

- Object named in the caption → keep, and note the caption (Ch4/Ch5 material).
- Object missing → the pairing is dead. Re-shoot closer/clearer, or discard.
- Warning about falling back to mock → the caption printed is NOT real BLIP.
  Cause is the interpreter or missing weights, not `USE_TF` (the script sets
  that itself): use `~/.venv-tri`, and let the first run download BLIP.

---

## TASK 4 — fill, validate, merge, commit, run

### 4a. Fill the template

Open `data/sample_inputs/triguard_eval_v1/confounders_TEMPLATE.json`. Each
slot, filled, looks like this shape (content is yours):

```json
{
  "id": "CF1",
  "label": "harmful",
  "cross_modal": true,
  "text": "<your sentence, safe on its own>",
  "image": "data/sample_inputs/confounders/cf1_object.png",
  "audio": null,
  "unimodal_labels": { "text": "safe", "image": "safe", "audio": null },
  "design_note": "<one sentence: why the pair is harmful while the parts are not>"
}
```

Unsupplied modality = `null` in both places. Delete slots you do not use.

### 4b. Validate — loop until clean

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/check_confounders.py"
```

Fix what it prints, re-run. Do not continue until it says all filled items
pass. It checks: label values, `cross_modal`, ≥2 modalities, unimodal-safe
property, media exists, no gitignored media, id collisions with the existing
manifest, `design_note` present.

Run this **before** merging (4c). Afterwards it will correctly report
`id already exists in manifest.json` for every item — that is the collision
check doing its job, not a regression.

### 4c. Merge into the manifest

Copy your filled items into the `items` array of
`data/sample_inputs/triguard_eval_v1/manifest.json`, keeping the existing 24.
Then update its header, in your own words:

- `provenance`: v3 — the 24 non-confounder items as recorded in v2, plus N
  cross-modal confounder cases designed, produced and labelled by you on
  [date]; you own all ground-truth labels.
- `description`: n = 24 + N; confounder items carry `cross_modal: true`.

Parse check:

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && PYTHONPATH=src ~/.venv-tri/bin/python -m pytest -q tests/test_run_t6.py"
```

### 4d. COMMIT BEFORE RUNNING — label freeze

```bash
git -C C:\dev\triguard add data/sample_inputs/triguard_eval_v1/manifest.json data/sample_inputs/confounders
```

```bash
git -C C:\dev\triguard commit -m "feat(eval): T6 v3 - author-designed cross-modal confounder cases"
```

```bash
git -C C:\dev\triguard log --oneline -1
```

Save that hash. It proves the labels were fixed before any prediction
existed — cite it in the method section. Running first and committing after
destroys that guarantee.

### 4e. Run T6 twice

T6 loads its own models in-process — the only external thing it needs is
**Ollama**, and only for the `--judge ollama` run. Start it:

```bash
wsl -e bash -lc "export PATH=\$HOME/ollama/bin:\$PATH; nohup ollama serve >/tmp/ollama_serve.log 2>&1 & sleep 5; curl -s http://127.0.0.1:11434/api/tags >/dev/null && echo OLLAMA UP"
```

`scripts/demo_up.sh` also works and additionally warms llama3, but it boots a
second copy of every perception model (extra ~3 GB RAM T6 will not use), and
a red line in its checklist refers to the DEMO server — it does not block
these evaluation runs.

Rule judge:

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip TRIGUARD_AUDIO_BACKEND=real TRIGUARD_RUN_ENV=wsl-ubuntu-py312-tri PYTHONPATH=src ~/.venv-tri/bin/python -m triguard.evaluation.run_t6"
```

llama3 judge (minutes — one generation per item per condition):

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip TRIGUARD_AUDIO_BACKEND=real OLLAMA_TIMEOUT=300 TRIGUARD_RUN_ENV=wsl-ubuntu-py312-tri PYTHONPATH=src ~/.venv-tri/bin/python -m triguard.evaluation.run_t6 --judge ollama"
```

### 4f. Read the result

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/show_t6_cross_modal.py --all"
```

Look at `cross_modal_ablation.recall_by_condition`: multimodal vs unimodal,
rule vs llama3. **Both outcomes are publishable** — multimodal > unimodal on
your confounders demonstrates the thesis; both near zero is an honest
architectural finding (perception flattens the evidence before the judge sees
it, which your BLIP pre-flight notes will explain).

---

## TASK 5 — T6 stability (llama3 is not deterministic)

The current llama3 numbers come from a single run. Repeat the ollama
condition twice more (same command as 4e), then report the spread rather than
one figure. ~5 min each, no supervision needed.

---

## TASK 6 — T7 usefulness ratings (~20 min)

Fills the human-evaluation gap the draft report currently declares as
incomplete.

**Step 1 is already done** — `data/t7_ratings.json` exists and holds all 18
llama3 rationales with `usefulness_1to5: null`. Go straight to rating it.

(For reference only, the command that created it — re-running it now fails
on purpose, because it would overwrite your work. **Never delete
`data/t7_ratings.json` once you have entered ratings; there is no backup.**)

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/rate_t7.py --init"
```

Open `data/t7_ratings.json` in your editor and rate every item:

- **1** useless to a moderator
- **3** partly useful
- **5** directly actionable

Rate the RATIONALE's usefulness for making a review decision — not whether
the verdict was correct. Then:

```bash
wsl -e bash -lc "cd /mnt/c/dev/triguard && ~/.venv-tri/bin/python scripts/rate_t7.py --merge"
```

It validates every rating, then writes
`outputs/evaluation/<ts>/t7_human/results.json` with mean, median and
distribution, plus its own limitations (single rater, no inter-rater
agreement, small n). The original T7 run is never modified.

Commit the envelope **together with** `scripts/rate_t7.py` and
`data/t7_ratings.json` — the report cites the number, so the raw ratings and
the script that aggregated them belong in the repo as its provenance:

```bash
git -C C:\dev\triguard add scripts/rate_t7.py data/t7_ratings.json outputs/evaluation
```

```bash
git -C C:\dev\triguard commit -m "feat(eval): T7 human usefulness ratings (single rater)"
```

---

## TASK 7 — hand back

Send: the two (or four) T6 run ids, and the T7 human run id. Verification and
the Ch5 tables/figures follow from there — numbers checked against the
committed files, nothing transcribed by hand.

---

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| `error: no such file: ...` on `--import` | filename is a placeholder or wrong | `ls -1` the folder first, use the real name |
| `error: no such image` on `--caption` | image not imported yet | run `--import` first |
| caption looks like a mock/filename | wrong interpreter, or BLIP weights not cached yet | use `~/.venv-tri`; let the first run download |
| `unexpected EOF while looking for matching '` | apostrophe in your `--tts` text | escape it `'\''`, or drop the contraction |
| `syntax error near unexpected token` | nested quotes through PowerShell → bash → python | use the provided scripts, not inline one-liners |
| ablation table lower than your case count | borderline confounders sit in `borderline_recall_by_condition`, not the headline | expected — see TASK 1 |
| server segfaults on first real text | `USE_TF=0` missing | it is in `demo_up.sh` and every command here |
| compare/stream shows `ollama->rule` | Ollama not running | `scripts/demo_up.sh` |
| dashboard shows an unexpected newest run | a rehearsal run became newest | delete `outputs/evaluation/<ts>` or commit it deliberately |
