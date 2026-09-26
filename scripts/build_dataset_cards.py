"""Build dataset cards (facts only) for the report from tracked sources.

    python scripts/build_dataset_cards.py                      # -> docs/dataset_cards.{json,md}
    python scripts/build_dataset_cards.py --out-dir <dir>      # write elsewhere (tests)
    python scripts/build_dataset_cards.py --cache-root <dir>   # also count rows in <dir>/t2_samples etc.
                                                               # (repeatable; NO default; never recorded)

Pure python: no ML imports, no network, no package import (the constants it
needs are read from the source files with `ast`). Every value is computed
from a named tracked file, a `git` command or a committed results.json; the
markdown carries a '## For integration' section with Table E10 (datasets and
tracks at a glance) and Table E11 (the 30-sentence bundled corpus card).

Nothing here is a judgement: authorship, reasons and interpretation are left
as [STUDENT] placeholders.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import hashlib
import json
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src" / "triguard"
_TEXT_MODEL = _SRC / "models" / "text_model.py"
_RUN_EVAL = _SRC / "evaluation" / "run_eval.py"
_DATASETS = _SRC / "data" / "datasets.py"
_IMAGE_DATASETS = _SRC / "data" / "image_datasets.py"
_AUDIO_DATASETS = _SRC / "data" / "audio_datasets.py"
_EVAL_DIR = _REPO / "data" / "sample_inputs" / "triguard_eval_v1"
_MANIFEST = _EVAL_DIR / "manifest.json"
_TEMPLATE = _EVAL_DIR / "confounders_TEMPLATE.json"
_OUTPUTS = _REPO / "outputs" / "evaluation"
_V1_COMMIT = "c8f22a8"  # T7/T8 evidence commit; manifest at that commit is the v1 set

_MODALITIES = ("text", "image", "audio")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _rel(p: Path) -> str:
    return p.resolve().relative_to(_REPO).as_posix()


def _git(*args: str) -> str:
    """Run git in the repo; return stdout stripped, or 'git unavailable: <err>'."""
    try:
        out = subprocess.run(["git", *args], cwd=str(_REPO), capture_output=True,
                             text=True, encoding="utf-8", check=True)
        return out.stdout.strip()
    except Exception as e:  # git missing / not a checkout
        return f"git unavailable: {type(e).__name__}"


def _ast_assign(path: Path, name: str) -> Any:
    """Return the literal value assigned to module-level ``name`` in ``path``.

    Also returns the 1-based (start, end) line span of the assignment.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name:
                value = ast.literal_eval(node.value)  # type: ignore[arg-type]
                return value, (node.lineno, node.end_lineno)
    raise KeyError(f"{name} not found in {path}")


def _line_of(path: Path, needle: str) -> Optional[int]:
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if needle in line:
            return i
    return None


def _combo(item: dict) -> str:
    return "+".join(m for m in _MODALITIES if item.get(m)) or "none"


def _hard_hits(text: str, tokens: list[str]) -> list[str]:
    lower = text.lower()
    return [t for t in tokens if t in lower]


# ---------------------------------------------------------------------------
# cards
# ---------------------------------------------------------------------------

def card_bundled_corpus() -> dict:
    train, span = _ast_assign(_TEXT_MODEL, "_TRAIN")
    tokens, tok_span = _ast_assign(_TEXT_MODEL, "_HARD_TOXIC_TOKENS")
    tokens = sorted(tokens)
    sentences = [s for s, _ in train]
    labels = [y for _, y in train]
    lengths = [len(s.split()) for s in sentences]
    first_tracked = _git("log", "--diff-filter=A", "--format=%h %ad",
                         "--", _rel(_TEXT_MODEL))
    return {
        "id": "A1",
        "name": "bundled 30-sentence corpus (sklearn tier training data)",
        "source_file": f"{_rel(_TEXT_MODEL)}:{span[0]}-{span[1]}",
        "role": "training-only (fits the TF-IDF + logistic-regression tier; never evaluated on)",
        "n": len(train),
        "per_label": {"non-toxic(0)": labels.count(0), "toxic(1)": labels.count(1)},
        "word_length": {"min": min(lengths), "mean": round(float(statistics.mean(lengths)), 2),
                        "max": max(lengths)},
        "sha256_joined_sentences": hashlib.sha256("\n".join(sentences).encode("utf-8")).hexdigest(),
        "hard_toxic_tokens": tokens,
        "hard_toxic_tokens_source": f"{_rel(_TEXT_MODEL)}:{tok_span[0]}-{tok_span[1]}",
        "authorship": None,
        "authorship_note": "STUDENT TO STATE (who wrote the 30 sentences and when)",
        "first_tracked_in_git": first_tracked,
        "first_tracked_note": "date the file entered version control; not a creation date",
        "licence": "repo code (tracked fixture); no external licence",
        "sentences": [{"text": s, "label": y, "hard_token_hits": _hard_hits(s, tokens)}
                      for s, y in train],
    }


def card_smoke_set(tokens: list[str]) -> dict:
    eval_set, span = _ast_assign(_RUN_EVAL, "EVAL_SET")
    label_counts = Counter(i["label"] for i in eval_set)
    combos = Counter(_combo(i) for i in eval_set)
    media = sorted({i[m] for i in eval_set for m in ("image", "audio") if i.get(m)})
    media_exist = {p: (_REPO / p.lstrip("/")).exists() for p in media}
    str_line = _line_of(_RUN_EVAL, "15 hand-built items")
    runs = []
    for r in sorted(_OUTPUTS.glob("*/results.json")):
        d = json.loads(r.read_text(encoding="utf-8"))
        runs.append({"run": r.parent.name, "n_samples": d.get("n_samples"),
                     "limitations[0]": (d.get("limitations") or [None])[0]})
    return {
        "id": "A2",
        "name": "T1/T5 hand-built smoke set (EVAL_SET)",
        "source_file": f"{_rel(_RUN_EVAL)}:{span[0]}-{span[1]}",
        "role": "evaluation (T1 wiring smoke run; mock image/audio, rule judge)",
        "n": len(eval_set),
        "per_label": dict(label_counts),
        "modality_combinations": dict(combos),
        "media_paths_referenced": media,
        "media_paths_exist_in_repo": media_exist,
        "string_vs_count": {
            "string": "15 hand-built items",
            "string_location": f"{_rel(_RUN_EVAL)}:{str_line}",
            "actual_len_EVAL_SET": len(eval_set),
        },
        "evidence_runs": runs,
        "items_with_hard_token": [i["id"] for i in eval_set
                                  if i.get("text") and _hard_hits(i["text"], tokens)],
        "licence": "repo code (tracked fixture); no external licence",
    }


def _loader_constants() -> dict:
    buf_t2, l_t2 = _ast_assign(_DATASETS, "_SHUFFLE_BUFFER")
    buf_t3, l_t3 = _ast_assign(_IMAGE_DATASETS, "_SHUFFLE_BUFFER")
    buf_t4, l_t4 = _ast_assign(_AUDIO_DATASETS, "_SHUFFLE_BUFFER")
    esc_map, l_map = _ast_assign(_AUDIO_DATASETS, "ESC50_TO_YAMNET")
    sources, l_src = _ast_assign(_DATASETS, "_SOURCES")
    formula_line = _line_of(_DATASETS, "buffer_size = min(_SHUFFLE_BUFFER")
    formula_text = _DATASETS.read_text(encoding="utf-8").splitlines()[formula_line - 1].strip()
    sample_size = 500
    return {
        "t2": {"shuffle_buffer": buf_t2, "line": f"{_rel(_DATASETS)}:{l_t2[0]}",
               "buffer_formula": formula_text,
               "buffer_formula_line": f"{_rel(_DATASETS)}:{formula_line}",
               "buffer_for_sample_size_500": min(buf_t2, max(sample_size * 20, 1000)),
               "shuffle_call_line": f"{_rel(_DATASETS)}:{_line_of(_DATASETS, '.shuffle(seed=seed, buffer_size=buffer_size)')}",
               "label_rule_line": f"{_rel(_DATASETS)}:{_line_of(_DATASETS, 'float(row[\"toxicity\"]) >= 0.5')}",
               "sources": sources, "sources_line": f"{_rel(_DATASETS)}:{l_src[0]}-{l_src[1]}"},
        "t3": {"shuffle_buffer": buf_t3, "line": f"{_rel(_IMAGE_DATASETS)}:{l_t3[0]}",
               "shuffle_call_line": f"{_rel(_IMAGE_DATASETS)}:{_line_of(_IMAGE_DATASETS, '.shuffle(seed=seed, buffer_size=_SHUFFLE_BUFFER)')}"},
        "t4": {"shuffle_buffer": buf_t4, "line": f"{_rel(_AUDIO_DATASETS)}:{l_t4[0]}",
               "esc50_to_yamnet_categories": len(esc_map),
               "esc50_to_yamnet_line": f"{_rel(_AUDIO_DATASETS)}:{l_map[0]}-{l_map[1]}",
               "esc50_mapped_categories": sorted(esc_map)},
    }


def _scan_envelopes() -> list[dict]:
    rows = []
    for r in sorted(_OUTPUTS.rglob("results.json")):
        d = json.loads(r.read_text(encoding="utf-8"))
        rel = _rel(r)
        run_id = r.parent.parent.name if r.parent.name.startswith("t") else r.parent.name
        cfg = d.get("config") or {}
        datasets: dict = {}
        if "dataset" in d:
            datasets["dataset"] = d["dataset"]
        if "datasets" in d:
            datasets = d["datasets"]
        n = d.get("n_samples", d.get("n_items", d.get("n")))
        if n is None and "whisper_wer" in d:
            n = {"whisper_wer": d["whisper_wer"].get("n"),
                 "yamnet_events": d["yamnet_events"].get("n")}
        rows.append({
            "track": d.get("track", "T1/T5 (no track key)"),
            "run_id": run_id,
            "path": rel,
            "run_at": d.get("run_at"),
            "datasets": datasets,
            "manifest": d.get("manifest"),
            "n": n,
            "class_balance": d.get("class_balance"),
            "config": {k: cfg.get(k) for k in ("sample_size", "seed", "threshold", "backend",
                                                "judge", "text_backend", "image_backend",
                                                "audio_backend", "run_env", "wrapper_mode",
                                                "mock") if k in cfg},
            "model_versions": d.get("model_versions"),
            "limitations": d.get("limitations"),
        })
    return rows


def _load_manifest_text(text: str) -> dict:
    m = json.loads(text)
    items = m["items"]
    return {
        "n": len(items),
        "per_label": dict(Counter(i["label"] for i in items)),
        "modality_combinations": dict(Counter(_combo(i) for i in items)),
        "cross_modal_count": sum(1 for i in items if i.get("cross_modal")),
        "provenance": m.get("provenance"),
        "description": m.get("description"),
        "ids": [i["id"] for i in items],
        "texts": [i["text"] for i in items if i.get("text")],
        "media": sorted({i[k] for i in items for k in ("image", "audio") if i.get(k)}),
    }


def card_eval_v1(envelopes: list[dict]) -> dict:
    raw = _git("show", f"{_V1_COMMIT}:{_rel(_MANIFEST)}")
    info = _load_manifest_text(raw)
    n = info["n"]
    direct = [e["run_id"] for e in envelopes
              if e["track"] == "T6" and e["n"] == n]
    inferred = [e["run_id"] for e in envelopes
                if e["track"] in ("T7", "T8") and e["n"] == n]
    return {
        "id": "A7",
        "name": "triguard_eval_v1 manifest, v1 (AI-drafted starter set)",
        "source": f"git show {_V1_COMMIT}:{_rel(_MANIFEST)}",
        "commit_shown": _git("log", "-1", "--format=%h %ad", _V1_COMMIT),
        "first_tracked_in_git": _git("log", "--diff-filter=A", "--format=%h %ad",
                                     "--", _rel(_MANIFEST)),
        "role": "evaluation (T6 v1 run; T7/T8 inputs)",
        **{k: info[k] for k in ("n", "per_label", "modality_combinations",
                                "cross_modal_count", "provenance", "media")},
        "evidence_runs_direct": direct,
        "evidence_runs_direct_note": "T6 envelope records manifest + manifest_provenance",
        "evidence_runs_inferred": inferred,
        "evidence_runs_inferred_note": (
            "inferred from n=18 + timestamps; envelopes do not record the manifest"),
        "licence": "repo fixture; media = committed benign self-made assets",
        "_texts": info["texts"],
    }


def card_eval_v2(envelopes: list[dict]) -> dict:
    info = _load_manifest_text(_MANIFEST.read_text(encoding="utf-8"))
    n = info["n"]
    direct = [e["run_id"] for e in envelopes if e["track"] == "T6" and e["n"] == n]
    return {
        "id": "A8",
        "name": "triguard_eval_v1 manifest, v2 (student-reviewed; current HEAD)",
        "source": _rel(_MANIFEST),
        "last_commit": _git("log", "-1", "--format=%h %ad", "--", _rel(_MANIFEST)),
        "role": "evaluation (T6 v2 runs, both judges)",
        **{k: info[k] for k in ("n", "per_label", "modality_combinations",
                                "cross_modal_count", "provenance", "media")},
        "evidence_runs_direct": direct,
        "licence": "repo fixture; media = committed benign self-made assets",
        "_texts": info["texts"],
    }


def card_confounder_template() -> dict:
    m = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    items = m["items"]
    filled = [i["id"] for i in items
              if i.get("label") is not None or any(i.get(k) for k in _MODALITIES)]
    return {
        "id": "A9",
        "name": "confounders_TEMPLATE.json (cross-modal confounder slots)",
        "source": _rel(_TEMPLATE),
        "role": "template only; never loaded by the harness (D-028); behind no reported number",
        "slots": len(items),
        "filled": len(filled),
        "filled_ids": filled,
        "provenance": m.get("provenance"),
        "last_commit": _git("log", "-1", "--format=%h %ad", "--", _rel(_TEMPLATE)),
    }


def _public_cards(consts: dict, envelopes: list[dict]) -> list[dict]:
    t2 = consts["t2"]
    cc = t2["sources"]["civil_comments"]
    t2_runs = [e for e in envelopes if e["track"] == "T2"]
    t3_runs = [e for e in envelopes if e["track"] == "T3"]
    t4_runs = [e for e in envelopes if e["track"] == "T4"]

    def _bal(runs: list[dict]) -> Any:
        bals = {json.dumps(e["class_balance"], sort_keys=True) for e in runs}
        return [json.loads(b) for b in bals]

    cards = [{
        "id": "A3", "name": "Civil Comments", "track": "T2",
        "hub_id": cc["hub_id"], "config": cc["config"], "licence": cc["licence"],
        "source_line": t2["sources_line"],
        "split": sorted({e["datasets"]["dataset"]["split"] for e in t2_runs}),
        "label_rule": "toxicity >= 0.5 -> 1 (toxic) else 0",
        "label_rule_line": t2["label_rule_line"],
        "selection": {"seed": sorted({e["config"].get("seed") for e in t2_runs}),
                      "cap": sorted({e["config"].get("sample_size") for e in t2_runs}),
                      "buffer": t2["buffer_for_sample_size_500"],
                      "buffer_formula": t2["buffer_formula"],
                      "filter": "non-empty text only (empty rows skipped)",
                      "sampling_frame_rows_consumed_approx": t2["buffer_for_sample_size_500"] + 500,
                      "wording": ("seeded buffered shuffle over a streaming iterator, buffer "
                                  "10,000; the 500 kept rows come from approximately the first "
                                  "10,500 rows of the shard-shuffled stream, not a uniform draw "
                                  "over the whole split; shard count not verified offline")},
        "n": sorted({e["n"] for e in t2_runs}),
        "class_balance": _bal(t2_runs),
        "class_balance_key": "class_balance",
        "evidence_runs": [{"run_id": e["run_id"], "backend": e["config"].get("backend"),
                           "wrapper_mode": e["config"].get("wrapper_mode"),
                           "run_env": e["config"].get("run_env", "not recorded")}
                          for e in t2_runs],
        "dataset_revision": "unpinned (datasets.py docstring: 'the dataset revision is not pinned')",
        "cache_file": "data/t2_samples/civil_comments_default_test_n500_seed42.json (gitignored)",
        "limitations_verbatim": {e["run_id"]: e["limitations"] for e in t2_runs},
    }, {
        "id": "A4", "name": "Memotion (MMSoc repack)", "track": "T3",
        "hub_id": t3_runs[0]["datasets"]["dataset"]["hub_id"] if t3_runs else None,
        "config": t3_runs[0]["datasets"]["dataset"]["config"] if t3_runs else None,
        "licence": t3_runs[0]["datasets"]["dataset"]["licence"] if t3_runs else None,
        "split": sorted({e["datasets"]["dataset"]["split"] for e in t3_runs}),
        "label_rule": "offensive field: 'not_*' -> 0 (not_offensive), anything else -> 1",
        "label_rule_line": f"{_rel(_IMAGE_DATASETS)}:{_line_of(_IMAGE_DATASETS, 'def _binarize_offensive')}",
        "selection": {"seed": sorted({e["config"].get("seed") for e in t3_runs}),
                      "cap": sorted({e["config"].get("sample_size") for e in t3_runs}),
                      "buffer": consts["t3"]["shuffle_buffer"],
                      "filter": "label parseable AND image present AND image decodable",
                      "sampling_frame_rows_consumed_approx": consts["t3"]["shuffle_buffer"] + 50},
        "n": sorted({e["n"] for e in t3_runs}),
        "class_balance": _bal(t3_runs),
        "class_balance_key": "class_balance",
        "evidence_runs": [e["run_id"] for e in t3_runs],
        "cache_file": "data/t3_samples/memotion_train_n50_seed42.json (gitignored)",
        "limitations_verbatim": {e["run_id"]: e["limitations"] for e in t3_runs},
    }, {
        "id": "A5", "name": "LibriSpeech test-clean", "track": "T4 (ASR / Whisper WER)",
        "hub_id": t4_runs[0]["datasets"]["librispeech"]["hub_id"] if t4_runs else None,
        "config": t4_runs[0]["datasets"]["librispeech"]["config"] if t4_runs else None,
        "licence": t4_runs[0]["datasets"]["librispeech"]["licence"] if t4_runs else None,
        "split": [t4_runs[0]["datasets"]["librispeech"]["split"]] if t4_runs else [],
        "label_rule": "none (reference transcript; WER task)",
        "selection": {"seed": sorted({e["config"].get("seed") for e in t4_runs}),
                      "cap": sorted({e["config"].get("sample_size") for e in t4_runs}),
                      "buffer": consts["t4"]["shuffle_buffer"],
                      "filter": "non-empty reference text AND audio array present",
                      "sampling_frame_rows_consumed_approx": consts["t4"]["shuffle_buffer"] + 50},
        "n": [e["n"]["whisper_wer"] for e in t4_runs],
        "class_balance": "n/a (ASR)",
        "evidence_runs": [e["run_id"] for e in t4_runs],
        "cache_file": "data/t4_samples/librispeech_clean_test_n50_seed42.json (gitignored)",
        "limitations_verbatim": {e["run_id"]: e["limitations"] for e in t4_runs},
    }, {
        "id": "A6", "name": "ESC-50", "track": "T4 (event tagging / YAMNet)",
        "hub_id": t4_runs[0]["datasets"]["esc50"]["hub_id"] if t4_runs else None,
        "config": t4_runs[0]["datasets"]["esc50"]["config"] if t4_runs else None,
        "licence": t4_runs[0]["datasets"]["esc50"]["licence"] if t4_runs else None,
        "split": [t4_runs[0]["datasets"]["esc50"]["split"]] if t4_runs else [],
        "label_rule": "category (string) kept as-is; hit = any mapped YAMNet name in top-k",
        "selection": {"seed": sorted({e["config"].get("seed") for e in t4_runs}),
                      "cap": sorted({e["config"].get("sample_size") for e in t4_runs}),
                      "buffer": consts["t4"]["shuffle_buffer"],
                      "filter": (f"category in ESC50_TO_YAMNET ({consts['t4']['esc50_to_yamnet_categories']} "
                                 "mapped categories) AND audio array present"),
                      "sampling_frame_rows_consumed_approx": (
                          f">= {consts['t4']['shuffle_buffer'] + 50} (unmapped categories are "
                          "skipped after being drawn; rows consumed not recorded)")},
        "n": [e["n"]["yamnet_events"] for e in t4_runs],
        "class_balance": "n/a (multi-category; see categories_used in envelope)",
        "evidence_runs": [e["run_id"] for e in t4_runs],
        "cache_file": "data/t4_samples/esc50_train_n50_seed42.json (gitignored)",
        "limitations_verbatim": {e["run_id"]: e["limitations"] for e in t4_runs},
    }]
    return cards


# ---------------------------------------------------------------------------
# optional cache check (path never recorded)
# ---------------------------------------------------------------------------

def _cache_check(cache_roots: list[Path], envelopes: list[dict]) -> dict:
    """Count rows/labels in persisted sample caches and compare with envelopes.

    The cache-root path is deliberately NOT written to the output.
    """
    def _find(rel: str) -> Optional[Path]:
        for root in cache_roots:
            p = root / rel
            if p.exists():
                return p
        return None

    if not cache_roots:
        return {"status": "no --cache-root given; caches not inspected"}

    def _t2() -> dict:
        p = _find("t2_samples/civil_comments_default_test_n500_seed42.json")
        if p is None:
            return {"status": "cache absent"}
        rows = json.loads(p.read_text(encoding="utf-8"))
        bal = {"non-toxic": sum(1 for r in rows if r["label"] == 0),
               "toxic": sum(1 for r in rows if r["label"] == 1)}
        env = [e["class_balance"] for e in envelopes if e["track"] == "T2"]
        return {"status": "present", "rows": len(rows), "class_balance": bal,
                "matches_every_T2_envelope": all(b == bal for b in env)}

    def _t3() -> dict:
        p = _find("t3_samples/memotion_train_n50_seed42.json")
        if p is None:
            return {"status": "cache absent"}
        rows = json.loads(p.read_text(encoding="utf-8"))
        bal = {"not_offensive": sum(1 for r in rows if r["label"] == 0),
               "offensive": sum(1 for r in rows if r["label"] == 1)}
        env = [e["class_balance"] for e in envelopes if e["track"] == "T3"]
        return {"status": "present", "rows": len(rows), "class_balance": bal,
                "matches_every_T3_envelope": all(b == bal for b in env)}

    def _t4() -> dict:
        out: dict = {}
        p = _find("t4_samples/librispeech_clean_test_n50_seed42.json")
        out["librispeech"] = ({"status": "cache absent"} if p is None else
                              {"status": "present",
                               "rows": len(json.loads(p.read_text(encoding="utf-8")))})
        p = _find("t4_samples/esc50_train_n50_seed42.json")
        if p is None:
            out["esc50"] = {"status": "cache absent"}
        else:
            rows = json.loads(p.read_text(encoding="utf-8"))
            cats = sorted({r["category"] for r in rows})
            env_cats = []
            for r in sorted(_OUTPUTS.rglob("results.json")):
                d = json.loads(r.read_text(encoding="utf-8"))
                if d.get("track") == "T4":
                    env_cats.append(sorted(d["yamnet_events"]["categories_used"]))
            out["esc50"] = {"status": "present", "rows": len(rows),
                            "distinct_categories": len(cats),
                            "categories_match_every_T4_envelope": all(c == cats for c in env_cats)}
        return out

    return {"status": "cache-root(s) given (path not recorded)",
            "t2": _t2(), "t3": _t3(), "t4": _t4()}


# ---------------------------------------------------------------------------
# overlap (computed, never typed)
# ---------------------------------------------------------------------------

def _overlap(corpus: dict, smoke_texts: list[str], v1_texts: list[str],
             v2_texts: list[str]) -> dict:
    tokens = corpus["hard_toxic_tokens"]
    train_lower = {s["text"].lower() for s in corpus["sentences"]}

    def _block(name: str, texts: list[str]) -> dict:
        lower = [t.lower() for t in texts]
        exact = sorted(t for t in lower if t in train_lower)
        hits = [t for t in texts if _hard_hits(t, tokens)]
        return {"set": name, "n_texts": len(texts),
                "exact_lowercase_matches_with_corpus": len(exact),
                "exact_match_texts": exact,
                "texts_with_>=1_hard_token": len(hits)}

    return {
        "corpus_sentences_with_>=1_hard_token": sum(
            1 for s in corpus["sentences"] if s["hard_token_hits"]),
        "corpus_toxic_sentences_with_>=1_hard_token": sum(
            1 for s in corpus["sentences"] if s["label"] == 1 and s["hard_token_hits"]),
        "vs": [_block("T1 EVAL_SET", smoke_texts),
               _block("T6 v1 manifest (c8f22a8)", v1_texts),
               _block("T6 v2 manifest (HEAD)", v2_texts)],
    }


# ---------------------------------------------------------------------------
# markdown
# ---------------------------------------------------------------------------

def _kv_table(d: dict, skip: tuple[str, ...] = ()) -> str:
    lines = ["| field | value |", "|---|---|"]
    for k, v in d.items():
        if k in skip or k.startswith("_"):
            continue
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        v = str(v).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def _fmt(v: Any) -> str:
    """Render a value for a markdown cell: unwrap 1-element lists, JSON for containers."""
    if isinstance(v, list) and len(v) == 1:
        v = v[0]
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _table_e10(cards: dict, corpus: dict, smoke: dict) -> str:
    hdr = ("| track | dataset | role | source id | licence | split | selection "
           "(seed/buffer/cap/filter; sampling frame = buffer + n rows consumed) | n | "
           "class balance | evidence run |\n|---|---|---|---|---|---|---|---|---|---|")
    rows = []
    t2 = cards["A3"]
    rows.append(
        f"| T2 (sklearn tier only) | {corpus['name']} | training-only | "
        f"`{corpus['source_file']}` | repo fixture | n/a | all 30 sentences, no sampling | "
        f"{corpus['n']} | {_fmt(corpus['per_label'])} | "
        f"{_fmt([e['run_id'] for e in t2['evidence_runs'] if e['backend'] in (None, 'sklearn')])} "
        f"(T1 runs do not record the text backend) |")
    rows.append(
        f"| T1/T5 | {smoke['name']} | evaluation (smoke) | `{smoke['source_file']}` | repo fixture | "
        f"n/a | hand-built, all items; media paths are filename cues only | {smoke['n']} | "
        f"{_fmt(smoke['per_label'])} | {_fmt([r['run'] for r in smoke['evidence_runs']])} |")
    sel = t2["selection"]
    t2_runs = [e["run_id"] + " (" + str(e["backend"] or e["wrapper_mode"]) + ")"
               for e in t2["evidence_runs"]]
    rows.append(
        f"| T2 | Civil Comments | evaluation | `{t2['hub_id']}` | {t2['licence']} | "
        f"{'/'.join(t2['split'])} | seed {_fmt(sel['seed'])} / buffer {sel['buffer']:,} / "
        f"cap {_fmt(sel['cap'])} / {sel['filter']}; frame ~{sel['sampling_frame_rows_consumed_approx']:,} rows | "
        f"{_fmt(t2['n'])} | {_fmt(t2['class_balance'])} | {_fmt(t2_runs)} |")
    for cid in ("A4", "A5", "A6"):
        c = cards[cid]
        sel = c["selection"]
        frame = sel["sampling_frame_rows_consumed_approx"]
        frame_s = f"~{frame:,} rows" if isinstance(frame, int) else f"{frame}"
        rows.append(
            f"| {c['track']} | {c['name']} | evaluation | `{c['hub_id']}`"
            f"{' / ' + c['config'] if c['config'] else ''} | {c['licence']} | "
            f"{'/'.join(c['split'])} | seed {_fmt(sel['seed'])} / buffer {sel['buffer']:,} / "
            f"cap {_fmt(sel['cap'])} / {sel['filter']}; frame {frame_s} | {_fmt(c['n'])} | "
            f"{_fmt(c['class_balance'])} | {_fmt(c['evidence_runs'])} |")
    for cid in ("A7", "A8"):
        c = cards[cid]
        runs = list(c["evidence_runs_direct"])
        inferred = c.get("evidence_runs_inferred", [])
        ev = _fmt(runs) + (f" + inferred {_fmt(inferred)}" if inferred else "")
        rows.append(
            f"| T6{' (+T7/T8)' if inferred else ''} | {c['name']} | evaluation | "
            f"`{c['source']}` | repo fixture | n/a | hand-built, all items; combos "
            f"{_fmt(c['modality_combinations'])} | {c['n']} | {_fmt(c['per_label'])} | {ev} |")
    return hdr + "\n" + "\n".join(rows)


def _table_e11(corpus: dict, overlap: dict) -> str:
    lines = ["| # | label | sentence (verbatim) | hard-token hits |", "|---|---|---|---|"]
    for i, s in enumerate(corpus["sentences"], 1):
        lines.append(f"| {i} | {s['label']} | {s['text']} | {', '.join(s['hard_token_hits']) or '-'} |")
    lines.append("")
    lines.append(f"Hard-token list (`{corpus['hard_toxic_tokens_source']}`, "
                 f"{len(corpus['hard_toxic_tokens'])} tokens): "
                 + ", ".join(corpus["hard_toxic_tokens"]))
    lines.append("")
    lines.append("| overlap check (computed) | T1 EVAL_SET | T6 v1 (c8f22a8) | T6 v2 (HEAD) |")
    lines.append("|---|---|---|---|")
    v = overlap["vs"]
    lines.append("| items with text | " + " | ".join(str(b["n_texts"]) for b in v) + " |")
    lines.append("| exact lowercase match with a corpus sentence | "
                 + " | ".join(str(b["exact_lowercase_matches_with_corpus"]) for b in v) + " |")
    lines.append("| items containing >= 1 hard token | "
                 + " | ".join(str(b["texts_with_>=1_hard_token"]) for b in v) + " |")
    lines.append("")
    lines.append(f"Corpus sentences containing >= 1 hard token: "
                 f"{overlap['corpus_sentences_with_>=1_hard_token']} of {corpus['n']} "
                 f"(toxic-labelled: {overlap['corpus_toxic_sentences_with_>=1_hard_token']} of "
                 f"{corpus['per_label']['toxic(1)']}).")
    return "\n".join(lines)


def _markdown(payload: dict) -> str:
    cards = payload["cards"]
    out = [
        "# Dataset cards (generated — facts only)",
        "",
        f"Generated by `scripts/build_dataset_cards.py` at git HEAD `{payload['git_head']}` "
        f"on {payload['generated_date']}. Do not edit by hand; re-run the script. "
        "Every value is read from the named file, computed by the script, or returned by `git`. "
        "Authorship, reasons and interpretation are [STUDENT] and are not stated here.",
        "",
        "Cache check: " + json.dumps(payload["cache_check"], ensure_ascii=False),
        "",
    ]
    order = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"]
    for cid in order:
        c = cards[cid]
        out.append(f"## {cid} — {c['name']}")
        out.append("")
        out.append(_kv_table(c, skip=("sentences", "limitations_verbatim")))
        if "limitations_verbatim" in c:
            out.append("")
            out.append("Limitations verbatim from the envelope(s):")
            for run, lims in c["limitations_verbatim"].items():
                for l in lims or []:
                    out.append(f"- `{run}`: {l}")
        out.append("")
    out.append("## Loader constants")
    out.append("")
    out.append(_kv_table({k: v for k, v in payload["loader_constants"]["t2"].items() if k != "sources"}))
    out.append("")
    out.append(_kv_table(payload["loader_constants"]["t3"]))
    out.append("")
    out.append(_kv_table({k: v for k, v in payload["loader_constants"]["t4"].items()
                          if k != "esc50_mapped_categories"}))
    out.append("")
    out.append("## Envelope scan (every committed results.json)")
    out.append("")
    out.append("| track | run id | n | class_balance | dataset(s) | config subset | model_versions |")
    out.append("|---|---|---|---|---|---|---|")
    for e in payload["envelopes"]:
        ds = e["datasets"] or e.get("manifest") or ""
        out.append(f"| {e['track']} | `{e['run_id']}` | {json.dumps(e['n'])} | "
                   f"{json.dumps(e['class_balance'])} | {json.dumps(ds, ensure_ascii=False)} | "
                   f"{json.dumps(e['config'])} | {json.dumps(e['model_versions'])} |")
    out.append("")
    out.append("## For integration")
    out.append("")
    out.append("### Table E10 — datasets & tracks at a glance (Ch5.1; only datasets behind a reported number)")
    out.append("")
    out.append(_table_e10(cards, cards["A1"], cards["A2"]))
    out.append("")
    out.append("A9 (confounder template, 12 slots / "
               f"{cards['A9']['filled']} filled) is behind no reported number and is excluded.")
    out.append("")
    out.append("### Table E11 — 30-sentence bundled corpus card (Ch4.2)")
    out.append("")
    out.append(f"Source `{cards['A1']['source_file']}`; role training-only; authorship: "
               f"{cards['A1']['authorship_note']}; first tracked in git: "
               f"`{cards['A1']['first_tracked_in_git']}`; sha256 of the newline-joined sentences "
               f"`{cards['A1']['sha256_joined_sentences'][:16]}…`.")
    out.append("")
    out.append(_table_e11(cards["A1"], payload["overlap"]))
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build(cache_roots: list[Path]) -> dict:
    corpus = card_bundled_corpus()
    smoke = card_smoke_set(corpus["hard_toxic_tokens"])
    consts = _loader_constants()
    envelopes = _scan_envelopes()
    public = {c["id"]: c for c in _public_cards(consts, envelopes)}
    v1 = card_eval_v1(envelopes)
    v2 = card_eval_v2(envelopes)
    template = card_confounder_template()
    smoke_texts = [i["text"] for i in _ast_assign(_RUN_EVAL, "EVAL_SET")[0] if i.get("text")]
    overlap = _overlap(corpus, smoke_texts, v1.pop("_texts"), v2.pop("_texts"))
    cards = {"A1": corpus, "A2": smoke, **public, "A7": v1, "A8": v2, "A9": template}
    return {
        "generated_by": "scripts/build_dataset_cards.py",
        "generated_date": _dt.date.today().isoformat(),
        "git_head": _git("rev-parse", "--short", "HEAD"),
        "cards": cards,
        "loader_constants": consts,
        "envelopes": envelopes,
        "overlap": overlap,
        "cache_check": _cache_check(cache_roots, envelopes),
    }


def main(argv: Optional[list[str]] = None) -> Path:
    p = argparse.ArgumentParser(description="Build TriGuard dataset cards (facts only)")
    p.add_argument("--out-dir", default=str(_REPO / "docs"),
                   help="where dataset_cards.json / .md are written (default docs/)")
    p.add_argument("--cache-root", action="append", default=[],
                   help="a data/ folder holding t2_samples/, t3_samples/, t4_samples/ "
                        "(repeatable; no default; the path is never written to the output)")
    args = p.parse_args(argv)
    payload = build([Path(r) for r in args.cache_root])
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dataset_cards.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = out_dir / "dataset_cards.md"
    md.write_text(_markdown(payload) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'dataset_cards.json'} and {md}")
    print(f"cache check: {json.dumps(payload['cache_check'])}")
    return md


if __name__ == "__main__":  # pragma: no cover
    sys.exit(0 if main() else 1)
