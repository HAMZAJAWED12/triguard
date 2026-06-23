---
title: "Literature Review for TriGuard: Multimodal, Explainable and Locally Deployable Content Moderation"
author: "Hamza — BSc Computer Science, University of London"
subtitle: "CM3070 Computer Science Final Project — CM3020 Artificial Intelligence Template, Project Idea 1: Orchestrating AI Models to Achieve a Goal"
date: "June 2026"
geometry: margin=2cm
fontsize: 11pt
mainfont: "Liberation Serif"
colorlinks: true
linkcolor: "blue"
urlcolor: "blue"
---

# 1. Introduction

Online platforms now host text, images, audio and video side by side, and harmful content frequently spans more than one modality at once (Kiela et al., 2020). Traditional automated moderators were designed to score a single signal — most commonly text — and struggle when a meme combines a benign caption with a hateful image, or when an innocuous post is wrapped around violent audio (Gorwa, Binns and Katzenbach, 2020). This survey reviews the work that informs **TriGuard**, a prototype CM3070 project that orchestrates three pre-trained perception models with a local Large Language Model (LLM) judge to produce a single, explainable moderation decision across text, image and audio. The review covers eight sources across text moderation, multimodal fusion, audio recognition, the LLM-as-judge paradigm, vision–language pre-training and the governance of algorithmic moderation. Each thematic section closes with a comparison paragraph that points toward the research gap TriGuard addresses.

# 2. Search Strategy and Selection Criteria

Sources were retrieved from the University of London Online Library, Google Scholar, the ACM Digital Library, the NeurIPS and ICML proceedings, and arXiv, using combinations of *content moderation*, *toxicity detection*, *multimodal hate speech*, *hateful memes*, *audio event detection*, *LLM-as-judge*, *explainable AI* and *algorithmic moderation*. Inclusion criteria were: (i) peer-reviewed or widely cited preprint with verifiable open weights, (ii) published 2017–2023, and (iii) contributes either a method TriGuard plans to use, a benchmark to evaluate against, or governance framing. Blog posts and product pages were excluded from primary citations.

# 3. Text-Based Moderation

The strongest production exemplar of text moderation is Google Jigsaw's **Perspective API**. Lees et al. (2022) replace the API's earlier per-language BERT classifiers with a single multilingual character-level transformer and report parity or improvement on internal toxicity benchmarks while serving billions of daily requests. Their account is significant for two reasons. First, it demonstrates that a single model can serve many languages — a property essential for any moderation system that hopes to be useful outside English. Second, it formalises the operational realities (latency budgets, fairness audits, drift monitoring) that academic moderation papers tend to ignore.

The limitation is structural rather than incidental. Perspective scores plain text. It cannot read a meme, cannot transcribe a voice note, and ships no human-readable rationale beyond a numeric probability per attribute. The system is closed-weights and cloud-only, which means platforms with privacy-sensitive content (medical, legal, child safeguarding) cannot deploy it without exposing user data to a third party. Compared to the multimodal and explainable work reviewed below, Perspective is best understood as a strong but deliberately narrow baseline — one that any new moderation pipeline must justify itself against on the text track, but that cannot, in isolation, satisfy the multimodal harms documented in §4–§5.

# 4. Image-Text and Hateful Meme Moderation

The single most influential resource for multimodal moderation research is the **Hateful Memes Challenge** introduced by Kiela et al. (2020). The benchmark contains roughly 10 000 memes constructed so that unimodal text classifiers and unimodal image classifiers score close to chance, forcing models to fuse modalities. Human accuracy is reported at approximately 85 %, while strong unimodal baselines reach only ~ 50 %. The first generation of multimodal baselines — VisualBERT (Li, L.H. et al., 2019) and ViLBERT — push performance into the mid-60s but remain substantially below humans, and the authors flag that synthetic "confounder" memes (where flipping a single token changes the label) defeat shortcuts that unimodal models rely on.

VisualBERT itself remains the canonical fusion baseline. Li, L.H. et al. (2019) propose a single-stream transformer that concatenates word embeddings and Faster-RCNN region features. The architecture is simple and reproducible — virtues that have made it a default starting point — but it is also brittle: caption quality depends on the region detector, and the only output is a class score with no rationale. **BLIP** (Li, J. et al., 2022) addresses the brittleness by removing the region-extraction stage and unifying captioning, retrieval and visual question answering inside one vision–language model with open weights. BLIP captions are short natural-language descriptions of an image, which is precisely the form an LLM judge can reason about.

Comparing across these works exposes a recurring pattern: the benchmark literature (Kiela et al., 2020) shows that fusion helps; the architecture literature (Li, L.H. et al., 2019; Li, J. et al., 2022) shows it is feasible with open components; yet none deliver an end-to-end moderation system or an output a human moderator could audit. Audio is absent from all three.

# 5. Audio and Speech-Based Moderation

Audio moderation is the least developed of the three modalities surveyed. **AudioSet** (Gemmeke et al., 2017) supplies the dominant ontology and benchmark — over two million 10-second clips across 632 sound classes — and the MobileNet/CNN baselines released alongside it (of which YAMNet is the most reused) provide pretrained features that work on a CPU. AudioSet is broad rather than safety-focused: it contains classes such as "shout", "explosion" and "screaming" that are relevant for moderation, but no fine-grained taxonomy of harm.

The complement on the speech side is **Whisper** (Radford et al., 2023), an encoder–decoder transformer trained on 680 000 hours of weakly supervised web audio. Whisper reports near-human English ASR and viable multilingual transcription across 96 languages, with open weights that run offline. Crucially for TriGuard, Whisper produces *text*, which can be fed into the text moderation track described in §3, avoiding the need to invent a new "audio toxicity" classifier.

Comparing the two: AudioSet/YAMNet gives a coarse event tag, while Whisper gives the words said; neither alone decides whether audio is harmful. The literature has not packaged speech-to-text and audio-event classification together for moderation, which is part of the gap TriGuard targets.

# 6. Model Orchestration and LLM-as-Judge Approaches

The orchestration layer that combines the three perception models draws on the **LLM-as-a-judge** literature. Zheng et al. (2023) systematically evaluate strong LLMs (GPT-4 in particular) as judges of open-ended responses on MT-Bench and Chatbot Arena. Their headline finding — that LLM judges agree with crowd-worker preferences roughly 80 % of the time — is matched by an equally important set of cautionary findings: judges exhibit *position bias* (preferring the first option presented), *verbosity bias* (preferring longer answers) and *self-preference bias* (preferring outputs from the same model family). Crucially, the authors show that these biases can be partially mitigated with calibration, swapped-order prompting and structured rubrics.

TriGuard adapts this pattern to a different setting. The judge does not compare two candidate answers; it reads a structured *evidence packet* (text toxicity scores, image caption, audio transcript + event tags) and returns a risk score, a risk label, the flagged modalities and a written rationale. Position and length bias are less acute when the input is fixed-format, but hallucinated reasoning — claims unsupported by the evidence — remains a live risk and motivates the prompt-engineering and JSON-schema enforcement TriGuard's design adopts.

Compared with the fusion-network approach of §4, the LLM-judge approach trades some accuracy headroom for a major qualitative gain: the decision is *expressible in natural language*. That gain becomes the bridge to the explainability and governance literature.

# 7. Explainability, Privacy, and Responsible Moderation

The technical literature so far treats moderation as a classification problem. **Gorwa, Binns and Katzenbach (2020)** reframe it as a sociotechnical one. Their survey distinguishes hash-matching, classifier-based, and policy-driven moderation, and argues that opaque automated decisions create governance failures — users denied due process, regulators unable to audit, platforms unable to explain themselves — that technical fixes alone do not solve. The paper predates the DSA and the UK Online Safety Act, but the transparency requirements those instruments codify (Statement of Reasons under DSA Article 17; risk-assessment duties under Article 34) closely track its concerns.

Read together with the technical works above, this paper sharpens the brief. A pipeline that scores well on Hateful Memes but cannot explain itself fails the governance test; one that explains itself but routes content through a closed cloud API fails the privacy test; one that is local and explainable but ignores audio fails the completeness test. The contribution of Gorwa, Binns and Katzenbach (2020) is to make these three failure modes legible as *requirements* rather than as nice-to-haves — the justification for TriGuard's two non-technical commitments: a human-readable rationale on every decision, and local-only deployment by default.

# 8. Comparative Analysis Table

The eight sources span complementary axes: modality coverage, output explainability, deployability and governance framing. The matrix below condenses that comparison.

| Source | Modality covered | Output type | Open weights | Explanation? |
|---|---|---|:---:|:---:|
| Lees et al. (2022) | Text | Class scores | No | No |
| Kiela et al. (2020) | Image + text | Benchmark labels | Yes | No |
| Li, L.H. et al. (2019) | Image + text | Class score | Yes | No |
| Gemmeke et al. (2017) | Audio | Event tags | Yes | No |
| Radford et al. (2023) | Audio (speech) | Text transcript | Yes | No |
| Zheng et al. (2023) | n/a (orchestration) | Judgement + rationale | Mixed | Yes |
| Li, J. et al. (2022) | Image + text | Caption | Yes | Indirectly |
| Gorwa et al. (2020) | n/a (governance) | n/a | n/a | Argues *for* explanation |

# 9. Research Gap

Synthesising across the matrix, the gap is concrete:

> *Existing moderation systems often focus on one modality or rely on closed cloud-based APIs. Prior multimodal work shows the value of combining text and image, but many systems do not include audio, do not run locally, and do not provide human-readable explanations. TriGuard addresses this gap by designing a local orchestration pipeline that combines text, image, and audio evidence and produces an explainable decision for human review.*

No single source surveyed delivers all four properties — **multimodal**, **audio-aware**, **explainable**, **locally deployable** — at once. TriGuard sits at their intersection.

# 10. How the Literature Informs TriGuard

Each source contributes a concrete design implication.

- **Lees et al. (2022)** justifies an off-the-shelf text classifier as the text-track baseline rather than training a new one.
- **Kiela et al. (2020)** supplies the image-text benchmark and quantifies the unimodal/fusion gap that motivates orchestration.
- **Li, L.H. et al. (2019)** is the academic fusion baseline against which TriGuard's LLM-judge approach must be contrasted.
- **Gemmeke et al. (2017)** supplies YAMNet weights and the event ontology for the audio wrapper.
- **Radford et al. (2023)** supplies Whisper so the text wrapper can be reused on audio content.
- **Zheng et al. (2023)** validates the LLM-as-judge pattern and identifies biases the prompt and schema must mitigate.
- **Li, J. et al. (2022)** supplies BLIP captions as the image-side input the judge needs.
- **Gorwa, Binns and Katzenbach (2020)** anchors the explainability and local-deployment requirements that distinguish TriGuard from a purely accuracy-driven prototype.

Together these works define both the methodological scaffold and the policy frame of the project. Each implication maps to a concrete component and evaluation track in Chapter 3.

# 11. References

Gemmeke, J.F., Ellis, D.P.W., Freedman, D., Jansen, A., Lawrence, W., Moore, R.C., Plakal, M. and Ritter, M. (2017) 'Audio Set: An ontology and human-labeled dataset for audio events', *Proceedings of the 2017 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*. New Orleans: IEEE, pp. 776–780. https://doi.org/10.1109/ICASSP.2017.7952261

Gorwa, R., Binns, R. and Katzenbach, C. (2020) 'Algorithmic content moderation: Technical and political challenges in the automation of platform governance', *Big Data & Society*, 7(1), pp. 1–15. https://doi.org/10.1177/2053951719897945

Kiela, D., Firooz, H., Mohan, A., Goswami, V., Singh, A., Ringshia, P. and Testuggine, D. (2020) 'The Hateful Memes Challenge: Detecting hate speech in multimodal memes', in *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. La Jolla: NeurIPS Foundation, pp. 2611–2624. arXiv:2005.04790.

Lees, A., Tran, V.Q., Tay, Y., Sorensen, J., Gupta, J., Metzler, D. and Vasserman, L. (2022) 'A new generation of Perspective API: Efficient multilingual character-level transformers', *Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '22)*. New York: ACM, pp. 3197–3207. https://doi.org/10.1145/3534678.3539147

Li, J., Li, D., Xiong, C. and Hoi, S. (2022) 'BLIP: Bootstrapping language–image pre-training for unified vision–language understanding and generation', in *Proceedings of the 39th International Conference on Machine Learning (ICML 2022)*. PMLR vol. 162, pp. 12888–12900. arXiv:2201.12086.

Li, L.H., Yatskar, M., Yin, D., Hsieh, C.J. and Chang, K.W. (2019) 'VisualBERT: A simple and performant baseline for vision and language', *arXiv preprint* arXiv:1908.03557.

Radford, A., Kim, J.W., Xu, T., Brockman, G., McLeavey, C. and Sutskever, I. (2023) 'Robust speech recognition via large-scale weak supervision', in *Proceedings of the 40th International Conference on Machine Learning (ICML 2023)*. PMLR vol. 202, pp. 28492–28518. arXiv:2212.04356.

Zheng, L., Chiang, W.L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E.P., Zhang, H., Gonzalez, J.E. and Stoica, I. (2023) 'Judging LLM-as-a-judge with MT-Bench and Chatbot Arena', in *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*. La Jolla: NeurIPS Foundation. arXiv:2306.05685.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            