# Referencing Notes — TriGuard

One block per source, using the CLAUDE.md §8 template.
Order matches `literature_matrix.md`. Harvard style.

---

## S1 — A new generation of Perspective API

**Full reference:**
Lees, A., Tran, V.Q., Tay, Y., Sorensen, J., Gupta, J., Metzler, D. and Vasserman, L. (2022) 'A new generation of Perspective API: Efficient multilingual character-level transformers', *Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '22)*. New York: ACM, pp. 3197–3207.

**Link/DOI:** arXiv:2202.11176 ; ACM DL: https://doi.org/10.1145/3534678.3539147
**Access date:** 2026-06-08
**Used in section:** §3 Text-Based Moderation; §8 Comparative Analysis; §9 Research Gap.

**Key idea:** Replaces older Perspective API models with multilingual character-level transformers; argues that a single multilingual model can outperform per-language BERT-based classifiers while serving billions of requests per day in production.

**Paraphrase notes:**
- Production system used by major newsrooms and platforms.
- Charformer-style architecture; trained on Jigsaw-curated comments.
- Authors acknowledge unintended bias and ongoing fairness auditing requirements.
- Text only — no image or audio.

**Reliability/credibility note:** Peer-reviewed at KDD 2022; authors include Jigsaw production engineers; widely-cited industry paper. Industry-affiliated; treat any claims about deployment success with normal caution.

---

## S2 — The Hateful Memes Challenge

**Full reference:**
Kiela, D., Firooz, H., Mohan, A., Goswami, V., Singh, A., Ringshia, P. and Testuggine, D. (2020) 'The Hateful Memes Challenge: Detecting hate speech in multimodal memes', in *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. La Jolla: NeurIPS Foundation, pp. 2611–2624.

**Link/DOI:** arXiv:2005.04790 ; https://proceedings.neurips.cc/paper/2020/hash/1b84c4cee2b8b3d823b30e2d604b1878-Abstract.html
**Access date:** 2026-06-08
**Used in section:** §4 Image-Text and Hateful Meme Moderation; §8 Comparative Analysis; §10 How the Literature Informs TriGuard.

**Key idea:** Introduces a benchmark of 10 000 multimodal memes designed so that unimodal text classifiers and unimodal image classifiers individually score near chance, forcing models to fuse text and image. Shows that humans reach ~85 % accuracy while strong unimodal models reach ~50 %, and that fusion baselines (VisualBERT, ViLBERT) improve but still trail humans.

**Paraphrase notes:**
- Gated/restricted dataset access — must register.
- Benchmark only; not a deployable moderation system.
- Audio is absent from the benchmark.
- Authors flag that synthetic "confounders" make the task harder than real-world memes.

**Reliability/credibility note:** Peer-reviewed NeurIPS 2020; Meta AI; one of the most-cited multimodal moderation papers.

---

## S3 — VisualBERT

**Full reference:**
Li, L.H., Yatskar, M., Yin, D., Hsieh, C.J. and Chang, K.W. (2019) 'VisualBERT: A simple and performant baseline for vision and language', *arXiv preprint* arXiv:1908.03557.

**Link/DOI:** https://arxiv.org/abs/1908.03557
**Access date:** 2026-06-08
**Used in section:** §4 Image-Text and Hateful Meme Moderation; §8 Comparative Analysis.

**Key idea:** Single-stream transformer that concatenates word embeddings and image-region features and trains with masked language modelling and image-text matching; becomes a standard fusion baseline reused across multimodal hate-speech tasks.

**Paraphrase notes:**
- Frozen-baseline status in Hateful Memes leaderboard.
- Tightly coupled to detected image regions (Faster-RCNN); brittle when regions are noisy.
- No explanation output; only a classification score.

**Reliability/credibility note:** arXiv preprint, but very widely cited (>3 000 citations); accepted as a methodological baseline across the field.

---

## S4 — AudioSet (and the YAMNet architecture line)

**Full reference:**
Gemmeke, J.F., Ellis, D.P.W., Freedman, D., Jansen, A., Lawrence, W., Moore, R.C., Plakal, M. and Ritter, M. (2017) 'Audio Set: An ontology and human-labeled dataset for audio events', *Proceedings of the 2017 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*. New Orleans: IEEE, pp. 776–780.

**Link/DOI:** https://doi.org/10.1109/ICASSP.2017.7952261
**Access date:** 2026-06-08
**Used in section:** §5 Audio and Speech-Based Moderation; §8 Comparative Analysis.

**Key idea:** Introduces AudioSet — over 2 million human-labelled 10-second clips across 632 sound event classes — and the YAMNet/MobileNet-style CNN baselines used to classify them. Establishes the dominant evaluation set for general-purpose audio event recognition.

**Paraphrase notes:**
- YAMNet (the model TriGuard plans to use) is trained on AudioSet.
- Generic audio events; not designed for speech-specific harm cues.
- Ontology is broad but skewed toward Western environments.

**Reliability/credibility note:** ICASSP 2017 (peer-reviewed); Google Research authors; foundational citation for audio-event work.

---

## S5 — Whisper

**Full reference:**
Radford, A., Kim, J.W., Xu, T., Brockman, G., McLeavey, C. and Sutskever, I. (2023) 'Robust speech recognition via large-scale weak supervision', in *Proceedings of the 40th International Conference on Machine Learning (ICML 2023)*. PMLR vol. 202, pp. 28492–28518.

**Link/DOI:** arXiv:2212.04356 ; https://proceedings.mlr.press/v202/radford23a.html
**Access date:** 2026-06-08
**Used in section:** §5 Audio and Speech-Based Moderation; §8 Comparative Analysis.

**Key idea:** Trains a 680 000-hour multilingual encoder–decoder for ASR using web-scale weak supervision; reports near-human zero-shot performance on out-of-distribution English speech and viable performance on 96 other languages.

**Paraphrase notes:**
- Open weights, runs locally.
- Strong transcription, but no toxicity classification — must be paired with downstream text moderation.
- Larger model sizes are heavy; small/base sizes are realistic for on-device use.

**Reliability/credibility note:** ICML 2023 (peer-reviewed); OpenAI; widely independently reproduced.

---

## S6 — LLM-as-a-Judge

**Full reference:**
Zheng, L., Chiang, W.L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E.P., Zhang, H., Gonzalez, J.E. and Stoica, I. (2023) 'Judging LLM-as-a-judge with MT-Bench and Chatbot Arena', in *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*. La Jolla: NeurIPS Foundation.

**Link/DOI:** arXiv:2306.05685 ; https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html
**Access date:** 2026-06-08
**Used in section:** §6 Model Orchestration and LLM-as-Judge; §10 How the Literature Informs TriGuard.

**Key idea:** Demonstrates that strong LLMs (e.g. GPT-4) agree with crowd-worker preferences with > 80 % alignment when used as judges on open-ended responses, but warns of position bias, verbosity bias, and self-preference bias. Argues that LLM judges are useful when paired with calibration and structured prompts.

**Paraphrase notes:**
- Validates the LLM-as-judge pattern that TriGuard adopts.
- Reports failure modes that TriGuard must mitigate: positional bias, hallucinated reasoning, length bias.
- The judge in TriGuard scores multimodal *evidence summaries*, not open-text quality — so position/length biases are less acute but hallucination is still a risk.

**Reliability/credibility note:** NeurIPS 2023 Datasets & Benchmarks Track; multi-institution authorship; reproducible code released.

---

## S7 — BLIP

**Full reference:**
Li, J., Li, D., Xiong, C. and Hoi, S. (2022) 'BLIP: Bootstrapping language–image pre-training for unified vision–language understanding and generation', in *Proceedings of the 39th International Conference on Machine Learning (ICML 2022)*. PMLR vol. 162, pp. 12888–12900.

**Link/DOI:** arXiv:2201.12086 ; https://proceedings.mlr.press/v162/li22n.html
**Access date:** 2026-06-08
**Used in section:** §4 Image-Text and Hateful Meme Moderation; §6 (methods); §8 Comparative Analysis.

**Key idea:** Introduces a single vision–language model that supports both understanding (image-text matching, VQA) and generation (image captioning). Reports state-of-the-art zero-shot captioning on COCO at the time of release and competitive image–text retrieval.

**Paraphrase notes:**
- TriGuard uses BLIP for image captioning so the LLM judge can reason on text.
- Authors caution that pre-training data biases propagate into captions — relevant for moderation.
- Lighter than VisualBERT pipelines because it does not need pre-extracted region features.

**Reliability/credibility note:** ICML 2022 (peer-reviewed); Salesforce Research; open weights and reproducible code.

---

## S8 — Algorithmic content moderation

**Full reference:**
Gorwa, R., Binns, R. and Katzenbach, C. (2020) 'Algorithmic content moderation: Technical and political challenges in the automation of platform governance', *Big Data & Society*, 7(1), pp. 1–15.

**Link/DOI:** https://doi.org/10.1177/2053951719897945
**Access date:** 2026-06-08
**Used in section:** §7 Explainability, Privacy, and Responsible Moderation; §9 Research Gap.

**Key idea:** Surveys the design of algorithmic moderation systems (matching, classifying, hashing), distinguishes "hard" vs "soft" moderation, and argues that opaque automated decisions create governance, due-process, and transparency problems that platforms have not solved. Frames moderation as a sociotechnical, not purely technical, problem.

**Paraphrase notes:**
- Provides the policy/ethics frame that TriGuard's "explainable + auditable" pitch responds to.
- Directly motivates the rationale-output requirement.
- Predates the EU Digital Services Act, but the concerns it raises are codified in DSA Articles 14, 17, 27 (transparency, statement of reasons).

**Reliability/credibility note:** *Big Data & Society* — peer-reviewed, open access; authors are established scholars at the Oxford Internet Institute and Weizenbaum Institute; extensively cited in tech-policy literature.

---

## Notes on credibility

- All eight sources are peer-reviewed venues or established preprints with high independent citation counts.
- No source is included unless I can open the PDF/abstract and verify the bibliographic details.
- Two sources (S1 Lees et al.; S5 Radford et al.) are industry-led — credibility note flags this.
- No web-only blog posts are cited in the literature review; product documentation (e.g. Perspective API docs, BLIP model card) is referenced as supporting material only inside §3–§7, not as primary citations.
