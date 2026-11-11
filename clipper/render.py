"""Cut a clip, lay it out 1080x1920 and burn in word-by-word captions with ffmpeg."""
import subprocess
from pathlib import Path

W, H = 1080, 1920
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
HIGHLIGHT = r"{\c&H00D7FF&}"  # gold, in ASS BGR order
WHITE = r"{\c&HFFFFFF&}"


def _ts(t: float) -> str:
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _clean(w: str) -> str:
    return w.replace("{", "").replace("}", "").replace("\\", "").upper()


def build_ass(words, clip_start, clip_end, path: Path, per_line=3, y=1430):
    lines = [ASS_HEAD]
    chunks = [words[i:i + per_line] for i in range(0, len(words), per_line)]
    for ci, chunk in enumerate(chunks):
        nxt = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else clip_end
        for wi, w in enumerate(chunk):
            start = w["s"] - clip_start
            end = (chunk[wi + 1]["s"] if wi + 1 < len(chunk) else min(nxt, w["e"] + 0.6)) - clip_start
            text = " ".join((HIGHLIGHT if k == wi else WHITE) + _clean(x["w"]) for k, x in enumerate(chunk))
            lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,{{\\an5\\pos(540,{y})}}{text}\n")
    path.write_text("".join(lines), encoding="utf-8")


def render(src: Path, start: float, end: float, words, out: Path, layout: str = "blur"):
    out.parent.mkdir(parents=True, exist_ok=True)
    ass = out.with_suffix(".ass")
    build_ass(words, start, end, ass)
    if layout == "crop":  # fill the frame, crop the sides (best when the speaker is centered)
        vf = f"scale=-2:{H},crop={W}:{H},ass={ass.name}"
    else:  # whole frame in the middle, blurred copy behind it (works for any video)
        vf = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=25:2[bg];"
              f"[b]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,ass={ass.name}")
    pre = max(start - 5, 0)  # fast seek near the start, then an exact seek after decoding
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{pre:.3f}", "-i", str(src.resolve()),
           "-ss", f"{start - pre:.3f}", "-t", f"{end - start:.3f}", "-vf", vf,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", out.name]
    subprocess.run(cmd, check=True, cwd=out.parent)  # run inside the output folder so the .ass path stays simple
    ass.unlink(missing_ok=True)
    return out
