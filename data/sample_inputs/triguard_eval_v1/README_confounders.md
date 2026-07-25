# Cross-modal confounder set — design guide

The confounder cases are the author's own evaluation design. This file
explains the CONCEPT and the mechanics; the cases, wording, media choices and
every label must be authored by the student.

## What a confounder is

A cross-modal confounder is an item where **each modality alone is benign but
the combination is harmful**. This is the design behind the Hateful Memes
benchmark (Kiela et al., 2020): their "benign confounders" flip the meaning
of a meme by swapping only the image or only the text, so unimodal models
cannot succeed. TriGuard's whole thesis — orchestration catches what unimodal
tools miss — is only demonstrated on items with this property.

The confounder property in manifest terms:

- `label` (the combination): `harmful` (or `borderline` for milder cases)
- `unimodal_labels`: each supplied modality alone rated `safe` (that is the
  point — if any single modality is already harmful, it is NOT a confounder;
  the v2 set already covers those)
- `cross_modal`: `true`

Recognised combination patterns (from the literature — the concrete cases are
yours to invent):

1. **Text recontextualises image** — neutral caption + neutral photo where the
   pairing creates mockery, threat or targeting.
2. **Image gives a target to generic text** — text with no target ("people
   like this should not exist") + photo identifying a group or person.
3. **Instruction + object** — innocuous imperative text + image of an object
   that together read as a threat or harmful instruction.
4. **Spoken words recontextualise text/image** — a TTS clip whose WORDING
   changes the meaning of the paired modality.

**Audio rail (important):** "tone of voice" does NOT work here. espeak output
is monotone; YAMNet tags acoustic events, not delivery; Whisper keeps only
the words. Prosody never reaches the judge — an audio confounder must carry
its recontextualisation in the transcript wording itself (pattern 4), or use
a YAMNet-taggable event. Design most items on patterns 1–3; use audio only
where the words do the work.

## Hard rules (ethics + repo)

- Media must be **benign in isolation and self-made or public-domain**: your
  own photos (no faces, no identifiable people/places, EXIF stripped — the
  import tool does this), synthetic images, or TTS speech clips.
- Genuinely disturbing media does NOT belong in this set — the harm should
  emerge from juxtaposition, which is exactly what makes the set publishable
  and committable. If an item needs shocking media to work, redesign it.
- Committed media lives in `data/sample_inputs/confounders/`. Nothing from
  `data/local_demo/` or `data/t3_samples/` may be referenced.
- **Fill all 12 slots if you can.** At n=8 every miss moves recall by 12.5
  percentage points; n=12 makes the numbers meaningfully less noisy. Balance
  patterns rather than repeating one trick.

## Workflow

1. Design your cases on paper first: for each, one sentence "why is the
   combination harmful while the parts are benign?" — that sentence goes in
   `design_note` and later feeds your report's method section.
2. Produce media with the toolkit (see `scripts/make_confounder_media.py`):
   - TTS clip: `--tts "the exact words to speak" --out cf1_calm_words.wav`
   - Own photo: `--import path/to/photo.jpg --out cf2_object.png`
     (resizes, converts, strips EXIF)
3. **BLIP pre-flight — before an image earns a slot**, caption it alone and
   keep the pairing only if the harm-carrying object survives in the one-line
   caption (WSL, models cached after first use):

   ```
   USE_TF=0 PYTHONPATH=src ~/.venv-tri/bin/python \
     scripts/make_confounder_media.py --caption data/sample_inputs/confounders/cf2_object.png
   ```

   If the caption drops the object your pairing depends on, the item is dead
   on arrival — discard or re-shoot before it costs a slot.
4. Fill `confounders_TEMPLATE.json` — every `null`, delete unused slots.
5. Validate: `python scripts/check_confounders.py` (structure, media exists,
   confounder property, id collisions vs manifest.json).
6. Merge the filled items into `manifest.json`'s `items` array, update the
   manifest `provenance` (your authorship statement + date), bump the
   `description`.
7. **COMMIT the merged manifest BEFORE the first T6 run on it.** The git
   timestamp is your label-freeze evidence: ground truth fixed before any
   prediction was seen. Cite the commit hash in the report's method section.
8. Re-run T6 twice and compare — this is the experiment:
   - rule judge (expected to miss most confounders — it scores modalities
     independently and only boosts when two already fired):
     `USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip TRIGUARD_AUDIO_BACKEND=real PYTHONPATH=src ~/.venv-tri/bin/python -m triguard.evaluation.run_t6`
   - llama3 judge (sees the evidence jointly; the interesting condition):
     same command + `--judge ollama` (Ollama must be running; OLLAMA_TIMEOUT=300)
9. Read `cross_modal_ablation.recall_by_condition` in the two results.json
   files. Both outcomes are report-worthy: llama3 > rule on confounders
   demonstrates the thesis; both low is an honest architectural finding about
   evidence-summary judges (the judge only sees wrapper OUTPUTS — a benign
   caption may already have destroyed the signal the combination carries).

That last caveat is worth understanding before you design: BLIP reduces the
image to a caption. If the harmful pairing depends on visual detail the
caption drops, no judge downstream can recover it. Cases whose image meaning
survives a one-line caption make the fairest test.
