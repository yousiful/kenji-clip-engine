"""Download a YouTube video (or take a local file) and return its path and title."""
from pathlib import Path

BLOCKED_HELP = """YouTube blocked this download ("Sign in to confirm you're not a bot").
This tool doesn't try to get around that. Use the original video file instead:
  - your own video: download it from YouTube Studio (Content > Options > Download)
  - a creator who gave you permission or runs a clipping program: use the source files they share
Then run: python clip.py path/to/video.mp4   (or a folder of videos)"""


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
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(source, download=True)
    except yt_dlp.utils.DownloadError as e:
        if "not a bot" in str(e) or "Sign in" in str(e):
            raise SystemExit(BLOCKED_HELP)
        raise
    return out / f"{info['id']}.mp4", info.get("title", info["id"])
