"""FastAPI demo surface for TriGuard.

A thin HTTP layer so a non-technical reviewer can submit content and read the
structured decision. Demo layer ONLY: it calls the existing orchestrator
(`triguard.orchestrator.pipeline.run`) and returns the `TriGuardResult` as JSON —
no wrapper, orchestrator or schema changes.

Backends honour the same env flags as the CLI (default mock / sklearn / rule,
fully offline). `judge_mode=None` is passed through so `TRIGUARD_JUDGE` is
respected (default rule); the API never forces real models.

Run (bind localhost only):
    uvicorn triguard.api.main:app --host 127.0.0.1 --port 8001
Then open http://127.0.0.1:8001/ui  (health JSON at http://127.0.0.1:8001/).
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Iterator, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ..models import llm_judge
from ..orchestrator.pipeline import VERSION, judge_label
from ..orchestrator.pipeline import run as run_pipeline
from ..orchestrator.schemas import JudgeInput, TriGuardResult

log = logging.getLogger("triguard.api")

app = FastAPI(title="TriGuard", version=VERSION)

_STATIC = Path(__file__).resolve().parent / "static"
# Repo root for the demo presets + committed eval outputs. Valid for the
# src-layout checkout this demo ships in; if the files are absent (e.g. a
# bare package install) the endpoints degrade gracefully instead of 500ing.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVAL_DIR = _REPO_ROOT / "outputs" / "evaluation"

# Whitelisted demo presets — committed sample JSONs ONLY. Never expand this
# to anything under data/t3_samples/ (untracked third-party meme media).
_PRESETS: dict[str, dict[str, str]] = {
    "safe": {
        "title": "Safe (mock cues)",
        "description": "Benign text; media paths are placeholders that drive "
                       "the deterministic mock wrappers.",
        "file": "data/sample_inputs/sample_safe.json",
    },
    "borderline": {
        "title": "Borderline (mock cues)",
        "description": "Rude-but-not-hateful text; placeholder media paths "
                       "(mock cues).",
        "file": "data/sample_inputs/sample_borderline.json",
    },
    "harmful": {
        "title": "Harmful cross-modal (mock cues)",
        "description": "Toxic text + weapon-image + violent-shout placeholder "
                       "paths (mock cues).",
        "file": "data/sample_inputs/sample_harmful.json",
    },
    "multimodal_real": {
        "title": "Real committed media",
        "description": "Real toxic sentence + the committed benign synthetic "
                       "image and speech clip; with real backends this is the "
                       "all-real integration demo.",
        "file": "data/sample_inputs/sample_multimodal_real.json",
    },
}


class TextRequest(BaseModel):
    text: str


@app.get("/")
def health() -> dict:
    """Liveness + version."""
    return {"status": "ok", "version": VERSION}


@app.get("/ui")
def ui() -> FileResponse:
    """Serve the single-page demo UI."""
    return FileResponse(str(_STATIC / "index.html"))


@app.post("/analyse/text")
def analyse_text(req: TextRequest) -> dict:
    """Analyse a piece of text; returns a TriGuardResult as JSON."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    result = run_pipeline(text=req.text, judge_mode=None)
    return result.model_dump()


def _save_upload(upload: UploadFile) -> str:
    """Persist an upload to a temp file; return its path (caller must unlink)."""
    suffix = Path(upload.filename or "").suffix
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(upload.file.read())
    return path


def _gather_inputs(
    text: Optional[str],
    image: Optional[UploadFile],
    audio: Optional[UploadFile],
) -> tuple[Optional[str], Optional[str], Optional[str], list[str]]:
    """Persist uploads and normalise the form; returns (txt, img, aud, tmp_paths).

    Caller must unlink every path in tmp_paths. Raises 400 if all absent.
    """
    tmp_paths: list[str] = []
    img_path: Optional[str] = None
    aud_path: Optional[str] = None
    try:
        if image is not None and image.filename:
            img_path = _save_upload(image)
            tmp_paths.append(img_path)
        if audio is not None and audio.filename:
            aud_path = _save_upload(audio)
            tmp_paths.append(aud_path)
    except Exception:
        # e.g. mkstemp rejects a client-controlled suffix — don't leak the
        # temp file(s) already saved for this request.
        _cleanup(tmp_paths)
        raise
    txt = text if (text and text.strip()) else None

    if txt is None and img_path is None and aud_path is None:
        _cleanup(tmp_paths)
        raise HTTPException(
            status_code=400,
            detail="provide at least one of text / image / audio",
        )
    return txt, img_path, aud_path, tmp_paths


def _cleanup(tmp_paths: list[str]) -> None:
    for p in tmp_paths:
        try:
            os.unlink(p)
        except OSError:
            pass


@app.post("/analyse/multimodal")
def analyse_multimodal(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
) -> dict:
    """Analyse any combination of text + image + audio; returns a TriGuardResult.

    Uploads are written to temp files, passed to the pipeline, then removed.
    """
    txt, img_path, aud_path, tmp_paths = _gather_inputs(text, image, audio)
    try:
        result = run_pipeline(
            text=txt, image=img_path, audio=aud_path, judge_mode=None
        )
        return result.model_dump()
    finally:
        _cleanup(tmp_paths)


# ---------------------------------------------------------------------------
# Phase D — demo presets
# ---------------------------------------------------------------------------


class PresetRequest(BaseModel):
    name: str


@app.get("/presets")
def list_presets() -> dict:
    """Whitelisted demo presets (committed sample inputs only)."""
    return {
        "presets": [
            {"name": name, "title": p["title"], "description": p["description"]}
            for name, p in _PRESETS.items()
        ]
    }


@app.post("/analyse/preset")
def analyse_preset(req: PresetRequest) -> dict:
    """Run one whitelisted committed sample through the pipeline.

    Relative media paths resolve against the repo root; the placeholder paths
    in the mock presets stay as-is (missing files degrade gracefully to the
    mock wrappers — honest via model_versions).
    """
    preset = _PRESETS.get(req.name)
    if preset is None:
        raise HTTPException(status_code=404,
                            detail=f"unknown preset '{req.name}'")
    sample_path = _REPO_ROOT / preset["file"]
    if not sample_path.is_file():
        raise HTTPException(status_code=503,
                            detail=f"sample file missing: {preset['file']}")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))

    def _resolve(p: Optional[str]) -> Optional[str]:
        if not p:
            return None
        candidate = _REPO_ROOT / p
        return str(candidate) if candidate.is_file() else p

    result = run_pipeline(
        text=sample.get("text"),
        image=_resolve(sample.get("image")),
        audio=_resolve(sample.get("audio")),
        judge_mode=None,
    )
    return {
        "preset": req.name,
        "inputs": sample,
        "result": result.model_dump(),
    }


# ---------------------------------------------------------------------------
# Phase D — side-by-side rule vs llama3 judge (perception runs ONCE)
# ---------------------------------------------------------------------------


def _judge_fields(r: TriGuardResult) -> dict:
    """The JudgeOutput-shaped slice of a TriGuardResult (no schema change)."""
    return {
        "risk_score": r.risk_score,
        "risk_label": r.risk_label,
        "flagged_modalities": r.flagged_modalities,
        "rationale": r.rationale,
        "uncertainties": r.uncertainties,
        "recommended_action": r.recommended_action,
    }


@app.post("/analyse/compare")
def analyse_compare(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
) -> dict:
    """Judge the SAME evidence twice: rule judge and Ollama/llama3.

    Perception (text/image/audio wrappers) runs once via the pipeline with
    the rule judge; the Ollama judge then re-scores the identical JudgeInput.
    If Ollama is unreachable its side falls back to the rule judge and is
    honestly labelled "ollama->rule".
    """
    txt, img_path, aud_path, tmp_paths = _gather_inputs(text, image, audio)
    try:
        rule_result = run_pipeline(
            text=txt, image=img_path, audio=aud_path, judge_mode="rule"
        )
    finally:
        _cleanup(tmp_paths)

    judge_input = JudgeInput(
        text=rule_result.text_evidence,
        image=rule_result.image_evidence,
        audio=rule_result.audio_evidence,
    )
    started = time.perf_counter()
    ollama_out = llm_judge.judge(judge_input, force_mode="ollama")
    ollama_ms = int((time.perf_counter() - started) * 1000)

    perception_versions = {
        k: v for k, v in rule_result.model_versions.items() if k != "llm_judge"
    }
    return {
        "note": "perception ran once; the same evidence was judged twice",
        "evidence": {
            "text": rule_result.text_evidence.model_dump()
            if rule_result.text_evidence else None,
            "image": rule_result.image_evidence.model_dump()
            if rule_result.image_evidence else None,
            "audio": rule_result.audio_evidence.model_dump()
            if rule_result.audio_evidence else None,
        },
        "perception_model_versions": perception_versions,
        "rule": {
            "judge_label": "rule",
            "latency_ms": rule_result.latency_ms,
            "output": _judge_fields(rule_result),
        },
        "ollama": {
            "judge_label": judge_label("ollama", ollama_out),
            "latency_ms": ollama_ms,
            "output": ollama_out.model_dump(),
        },
    }


# ---------------------------------------------------------------------------
# Phase D — streaming llama3 judge (SSE; presentation-only token stream)
# ---------------------------------------------------------------------------


@app.post("/analyse/stream")
def analyse_stream(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
) -> StreamingResponse:
    """Run perception once, then stream the Ollama judge as SSE events.

    Events (each a `data: <json>` line):
      {"type": "evidence", ...}  — evidence + instant rule verdict, first;
      {"type": "token", ...}     — llama3 fragments (presentation only);
      {"type": "final", ...}     — the authoritative schema-validated verdict,
                                   with source "ollama" or "rule_fallback"
                                   and the matching honest judge_label.

    Perception + temp-file cleanup happen BEFORE streaming starts, so a
    client disconnect cannot leak temp files.
    """
    txt, img_path, aud_path, tmp_paths = _gather_inputs(text, image, audio)
    try:
        rule_result = run_pipeline(
            text=txt, image=img_path, audio=aud_path, judge_mode="rule"
        )
    finally:
        _cleanup(tmp_paths)

    judge_input = JudgeInput(
        text=rule_result.text_evidence,
        image=rule_result.image_evidence,
        audio=rule_result.audio_evidence,
    )

    def _events() -> Iterator[str]:
        first = {
            "type": "evidence",
            "evidence": {
                "text": rule_result.text_evidence.model_dump()
                if rule_result.text_evidence else None,
                "image": rule_result.image_evidence.model_dump()
                if rule_result.image_evidence else None,
                "audio": rule_result.audio_evidence.model_dump()
                if rule_result.audio_evidence else None,
            },
            "perception_model_versions": {
                k: v for k, v in rule_result.model_versions.items()
                if k != "llm_judge"
            },
            "rule": {
                "judge_label": "rule",
                "latency_ms": rule_result.latency_ms,
                "output": _judge_fields(rule_result),
            },
        }
        yield f"data: {json.dumps(first)}\n\n"
        for event in llm_judge.judge_stream(judge_input):
            if event.get("type") == "final":
                event["judge_label"] = (
                    "ollama" if event.get("source") == "ollama"
                    else "ollama->rule"
                )
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(_events(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Phase D — evaluation dashboard (numbers read from committed results.json
# files ONLY; nothing is computed or invented here)
# ---------------------------------------------------------------------------

# Per-track whitelist of keys copied VERBATIM from results.json into the
# summary. Bulky per-sample arrays are dropped; no value is transformed.
_TRACK_KEYS: dict[str, tuple[str, ...]] = {
    "t2": ("run_at", "dataset", "n_samples", "class_balance", "config",
           "model_versions", "accuracy", "macro_f1", "per_class",
           "limitations"),
    "t3": ("run_at", "dataset", "n_samples", "class_balance", "config",
           "model_versions", "metrics_pipeline", "metrics_text_only_baseline",
           "ocr_ablation", "limitations"),
    "t4": ("run_at", "datasets", "config", "model_versions", "limitations"),
    "t6": ("run_at", "n_items", "class_balance", "config",
           "manifest_provenance", "cross_modal_ablation", "limitations"),
    "t7": ("run_at", "judge", "n", "grounding_rate",
           "invented_modality_count", "config", "note"),
    "t8": ("run_at", "n", "config", "latency_ms", "peak_rss_mb", "note"),
}


def _trim_track(track: str, data: dict) -> dict:
    """Whitelist-copy the headline fields of one results.json, verbatim."""
    out = {k: data[k] for k in _TRACK_KEYS.get(track, ()) if k in data}
    if track == "t4":
        wer = data.get("whisper_wer", {})
        out["whisper_wer"] = {k: wer[k] for k in
                              ("n", "wer_corpus", "wer_mean_per_clip")
                              if k in wer}
        yam = data.get("yamnet_events", {})
        out["yamnet_events"] = {k: yam[k] for k in
                                ("n", "top1_rate", "top5_rate") if k in yam}
    if track == "t6":
        conditions = data.get("conditions", {})
        out["conditions"] = {
            name: {k: cond[k] for k in
                   ("n", "accuracy", "macro_f1", "latency_ms") if k in cond}
            for name, cond in conditions.items()
        }
    return out


@app.get("/eval/summary")
def eval_summary() -> dict:
    """Headline numbers of the latest committed run per evaluation track.

    Scans outputs/evaluation/<ts>/t*/results.json. T2 is kept per backend
    (sklearn baseline vs hf) and T8 per config (mock vs real); for every
    other track the newest run wins. Values are copied verbatim — the
    limitations / provenance strings ride along with the numbers.
    """
    if not _EVAL_DIR.is_dir():
        return {"available": False,
                "reason": "outputs/evaluation not found on this checkout"}

    tracks: dict[str, dict] = {}
    t2_by_backend: dict[str, dict] = {}
    t8_by_config: dict[str, dict] = {}

    for run_dir in sorted(p for p in _EVAL_DIR.iterdir() if p.is_dir()):
        for track_dir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
            results = track_dir / "results.json"
            if not results.is_file():
                continue
            try:
                data = json.loads(results.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                log.warning("skipping unreadable %s: %s", results, e)
                continue
            track = str(data.get("track", track_dir.name)).lower()
            entry = {
                "run": run_dir.name,
                "file": results.relative_to(_REPO_ROOT).as_posix(),
                "data": _trim_track(track, data),
            }
            if track == "t2":
                backend = (data.get("config", {}).get("backend")
                           or ("sklearn" if "sklearn" in str(
                               data.get("model_versions", {})
                               .get("text_model", "")) else "unknown"))
                t2_by_backend[backend] = entry  # sorted scan -> newest wins
            elif track == "t8":
                mock_val = data.get("config", {}).get("mock")
                cfg = ("mock" if mock_val is True
                       else "real" if mock_val is False else "unknown")
                t8_by_config[cfg] = entry
            else:
                tracks[track] = entry

    if t2_by_backend:
        tracks["t2"] = {"runs_by_backend": t2_by_backend}
    if t8_by_config:
        tracks["t8"] = {"runs_by_config": t8_by_config}

    return {
        "available": bool(tracks),
        "source": ("outputs/evaluation results.json files on this checkout, "
                   "read verbatim (git-committed status is not checked — "
                   "verify the run ids against the committed evidence)"),
        "tracks": tracks,
    }


@app.get("/dashboard")
def dashboard() -> FileResponse:
    """Serve the evaluation dashboard page."""
    return FileResponse(str(_STATIC / "dashboard.html"))
