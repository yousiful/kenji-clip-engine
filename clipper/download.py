"""Download a YouTube video (or take a local file) and return its path and title."""
from pathlib import Path


def get_source(source: str, out_dir: str = "downloads"):
    p = Path(source)
    if p.exists():
        return p, p.stem
    import yt_dlp
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    opts = {
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(out / "%(id)s.%(ext)s"),
        "quiet": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(source, download=True)
    return out / f"{info['id']}.mp4", info.get("title", info["id"])
