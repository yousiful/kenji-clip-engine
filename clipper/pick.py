"""Pick clip windows from a transcript.

Manual: "1:20-2:05,5:00-5:45".
Auto: score every window that starts and ends on a sentence boundary
(so a clip never ends mid-thought) and keep the best ones that don't overlap.
"""
import re

HOOK_WORDS = {
    "you", "your", "how", "why", "what", "secret", "mistake", "never", "stop", "truth",
    "money", "free", "first", "best", "worst", "nobody", "everyone", "here's", "this",
    "because", "if", "biggest", "fastest", "simple", "easy", "wrong", "real",
}


def parse_time(t: str) -> float:
    parts = [float(x) for x in t.strip().split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def manual(spec: str):
    clips = []
    for part in spec.split(","):
        a, b = part.split("-")
        clips.append((parse_time(a), parse_time(b)))
    return clips


def _score(segs):
    words = [w for s in segs for w in s["words"]]
    if not words:
        return 0
    dur = segs[-1]["end"] - segs[0]["start"]
    opening = " ".join(w["w"].lower() for w in words if w["s"] < segs[0]["start"] + 5)
    hook = sum(1 for t in re.findall(r"[a-z']+", opening) if t in HOOK_WORDS)
    question = 2 if "?" in segs[0]["text"] else 0
    numbers = min(len(re.findall(r"\d|\$|percent", " ".join(s["text"] for s in segs))), 4)
    pace = len(words) / max(dur, 1)  # energetic speech scores higher
    ends_clean = 1 if segs[-1]["text"].rstrip().endswith((".", "!", "?")) else -2
    return hook * 1.5 + question + numbers + pace * 2 + ends_clean


def auto(transcript, count=3, min_len=25, max_len=60):
    candidates = []
    n = len(transcript)
    for i in range(n):
        for j in range(i, n):
            dur = transcript[j]["end"] - transcript[i]["start"]
            if dur > max_len:
                break
            if dur >= min_len:
                candidates.append((_score(transcript[i:j + 1]), transcript[i]["start"], transcript[j]["end"]))
    candidates.sort(reverse=True)
    picked = []
    for score, a, b in candidates:
        if all(b <= pa or a >= pb for pa, pb in picked):
            picked.append((a, b))
        if len(picked) == count:
            break
    return sorted(picked)


def words_between(transcript, a, b):
    return [w for s in transcript for w in s["words"] if w["s"] >= a - 0.05 and w["e"] <= b + 0.05]
