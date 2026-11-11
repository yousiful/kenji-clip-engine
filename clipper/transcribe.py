"""Word-level transcript with faster-whisper. Cached next to the video as <name>.words.json."""
import json
from pathlib import Path


def transcribe(video: Path, model: str = "small", gpu: bool = False):
    cache = video.with_suffix(".words.json")
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cuda" if gpu else "cpu", compute_type="float16" if gpu else "int8")
    segments, _ = m.transcribe(str(video), word_timestamps=True, vad_filter=True)
    out = []
    for s in segments:
        words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for w in (s.words or []) if w.word.strip()]
        if words:
            out.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(), "words": words})
    cache.write_text(json.dumps(out), encoding="utf-8")
    return out
