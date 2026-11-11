"""Turn a YouTube video (or a local file) into vertical, captioned clips.

  python clip.py "https://www.youtube.com/watch?v=VIDEO_ID" --auto 3
  python clip.py "https://youtu.be/VIDEO_ID" --clips "1:20-2:05,7:40-8:30"
  python clip.py my_webinar.mp4 --auto 5 --layout crop
  python clip.py "https://youtu.be/VIDEO_ID" --auto 3 --post        (clip, then push to Kenji)
"""
import argparse
import json
import re
from pathlib import Path

from dotenv import load_dotenv

from clipper import pick
from clipper.download import get_source
from clipper.render import render
from clipper.transcribe import transcribe


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "clip"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="YouTube URL or a local video file")
    ap.add_argument("--auto", type=int, default=3, help="how many clips to pick automatically (default 3)")
    ap.add_argument("--clips", help='pick clips yourself: "1:20-2:05,7:40-8:30"')
    ap.add_argument("--min", type=float, default=25, help="shortest auto clip in seconds (default 25)")
    ap.add_argument("--max", type=float, default=60, help="longest auto clip in seconds (default 60)")
    ap.add_argument("--layout", choices=["blur", "crop"], default="blur",
                    help="blur = full frame with blurred background, crop = fill the screen (speaker centered)")
    ap.add_argument("--model", default="small", help="whisper model: tiny, base, small, medium, large-v3")
    ap.add_argument("--gpu", action="store_true", help="transcribe on an NVIDIA GPU")
    ap.add_argument("--out", default="output", help="output folder (default output/)")
    ap.add_argument("--post", action="store_true", help="push the finished clips to Kenji right after")
    args = ap.parse_args()

    print("1/4  Getting the video...")
    video, title = get_source(args.source)
    print(f"     {title}")

    print("2/4  Transcribing (first run downloads the speech model)...")
    transcript = transcribe(video, args.model, args.gpu)
    if not transcript:
        raise SystemExit("No speech found in this video.")

    print("3/4  Picking clips...")
    windows = pick.manual(args.clips) if args.clips else pick.auto(transcript, args.auto, args.min, args.max)
    if not windows:
        raise SystemExit("Couldn't find clips that fit. Try --min 15 or pick times with --clips.")

    print(f"4/4  Rendering {len(windows)} clip(s)...")
    out_dir = Path(args.out)
    made = []
    for i, (a, b) in enumerate(windows, 1):
        words = pick.words_between(transcript, a, b)
        hook = " ".join(w["w"] for w in words[:14]).strip()
        path = render(video, a, b, words, out_dir / f"{slug(title)}-{i}.mp4", args.layout)
        made.append({"file": str(path), "start": round(a, 2), "end": round(b, 2), "hook": hook,
                     "caption": f"{hook}...\n\nFull video: {args.source}" if args.source.startswith("http") else f"{hook}..."})
        print(f"     {path}  ({b - a:.0f}s)  \"{hook[:60]}\"")

    manifest = out_dir / "clips.json"
    manifest.write_text(json.dumps(made, indent=2), encoding="utf-8")
    print(f"\nDone. {len(made)} clip(s) in {out_dir}/  Captions to edit are in {manifest}")

    if args.post:
        load_dotenv()
        from post import post_clips
        post_clips(made)


if __name__ == "__main__":
    main()
