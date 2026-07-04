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

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..orchestrator.pipeline import VERSION
from ..orchestrator.pipeline import run as run_pipeline

app = FastAPI(title="TriGuard", version=VERSION)

_STATIC = Path(__file__).resolve().parent / "static"


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


@app.post("/analyse/multimodal")
def analyse_multimodal(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
) -> dict:
    """Analyse any combination of text + image + audio; returns a TriGuardResult.

    Uploads are written to temp files, passed to the pipeline, then removed.
    """
    tmp_paths: list[str] = []
    try:
        img_path: Optional[str] = None
        aud_path: Optional[str] = None
        if image is not None and image.filename:
            img_path = _save_upload(image)
            tmp_paths.append(img_path)
        if audio is not None and audio.filename:
            aud_path = _save_upload(audio)
            tmp_paths.append(aud_path)
        txt = text if (text and text.strip()) else None

        if txt is None and img_path is None and aud_path is None:
            raise HTTPException(
                status_code=400,
                detail="provide at least one of text / image / audio",
            )

        result = run_pipeline(
            text=txt, image=img_path, audio=aud_path, judge_mode=None
        )
        return result.model_dump()
    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass
