"""
Audio wrapper for TriGuard — mock for the prototype.

The real implementation will call OpenAI Whisper (transcription) and YAMNet
(audio event tagging). The mock returns a deterministic transcript and event
list derived from the file name.
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from ..orchestrator.schemas import AudioEvidence

_AUDIO_TAGS = {
    "shout": ("shouting", 0.7),
    "scream": ("screaming", 0.8),
    "gun": ("gunshot", 0.75),
    "siren": ("siren", 0.6),
    "calm": ("speech", 0.6),
    "speech": ("speech", 0.7),
}


def analyse(audio: Union[str, Path]) -> AudioEvidence:
    path = Path(audio)
    name = path.stem.lower().replace("-", " ").replace("_", " ")

    tags: list[tuple[str, float]] = []
    for token, (label, conf) in _AUDIO_TAGS.items():
        if token in name:
            tags.append((label, conf))

    # Heuristic transcript: name itself as the apparent content.
    if "shout" in name or "scream" in name:
        transcript = "(loud distressed vocalisation)"
        transcript_conf = 0.35
    elif "speech" in name or "calm" in name:
        transcript = f"sample speech about {name}"
        transcript_conf = 0.6
    else:
        transcript = f"unclear audio with hints of {name}"
        transcript_conf = 0.45

    return AudioEvidence(
        transcript=transcript,
        transcript_confidence=transcript_conf,
        yamnet_tags=tags,
        raw={"mode": "mock", "path": str(path)},
    )
