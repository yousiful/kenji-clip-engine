"""Push clips to Kenji AI. Kenji's Social Planner posts each one to every connected account.

  python post.py                                   (everything in output/clips.json, asks before posting)
  python post.py --dry-run                         (show what would post, send nothing)
  python post.py --only tiktok,instagram,youtube   (pick platforms)
  python post.py --schedule "2026-11-12 09:30"     (local time; one clip per day from that time)
  python post.py output/my-clip-1.mp4 --caption "Watch this before your next launch"
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from clipper.kenji import Kenji

# Video platforms. Kenji also lists Google Business and Community groups; add them with --only if you want them.
DEFAULT_PLATFORMS = {"facebook", "instagram", "tiktok", "youtube", "linkedin", "pinterest"}


def to_utc(local_str, plus_days=0):
    t = datetime.strptime(local_str, "%Y-%m-%d %H:%M").astimezone() + timedelta(days=plus_days)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def post_clips(clips, only=None, schedule=None, dry_run=False, yes=False):
    k = Kenji()
    accounts = [a for a in k.accounts() if a.get("platform") in (only or DEFAULT_PLATFORMS)]
    if not accounts:
        raise SystemExit("No connected accounts to post to. Connect them in Kenji first (README, Step 2).")

    print(f"\nKenji will post to {len(accounts)} account(s):")
    for a in accounts:
        print(f"   {a.get('platform', '?'):<10} {a.get('name', '')}")
    print()
    for i, c in enumerate(clips):
        when = to_utc(schedule, i) + " (UTC)" if schedule else "right away"
        print(f" - {Path(c['file']).name}  ->  {when}\n   \"{c['caption'][:90]}\"")
    if dry_run:
        print("\nDry run. Nothing was uploaded or posted.")
        return
    if not yes and input("\nPost these? Type yes: ").strip().lower() != "yes":
        print("Cancelled.")
        return

    for i, c in enumerate(clips):
        print(f"\nUploading {Path(c['file']).name} to your Kenji media library...")
        url = k.upload(c["file"])
        res = k.post(url, c["caption"], accounts, to_utc(schedule, i) if schedule else None, c.get("hook"))
        for group, n, _ in res:
            print(f"   sent to {n} {group} account(s)")
    print("\nDone. Open Kenji > Marketing > Social Planner to see every post and its status.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="clip files (default: everything in output/clips.json)")
    ap.add_argument("--caption", help="caption for the files you list")
    ap.add_argument("--only", help="comma list (default: facebook,instagram,tiktok,youtube,linkedin,pinterest). Also: google, community")
    ap.add_argument("--schedule", help='first post time, local: "YYYY-MM-DD HH:MM". Later clips go one per day.')
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation question")
    args = ap.parse_args()
    load_dotenv()

    if args.files:
        clips = [{"file": f, "caption": args.caption or Path(f).stem.replace("-", " ")} for f in args.files]
    else:
        manifest = Path("output/clips.json")
        if not manifest.exists():
            sys.exit("No output/clips.json yet. Run clip.py first, or list files: python post.py my-clip.mp4")
        clips = json.loads(manifest.read_text(encoding="utf-8"))
    only = set(args.only.split(",")) if args.only else None
    post_clips(clips, only, args.schedule, args.dry_run, args.yes)


if __name__ == "__main__":
    main()
