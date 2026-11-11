"""Small client for the Kenji AI (GHL) API: media upload and Social Planner posts."""
import os
import requests

BASE = "https://services.leadconnectorhq.com"


class Kenji:
    def __init__(self, api_key=None, location_id=None, user_id=None):
        self.key = api_key or os.environ.get("KENJI_API_KEY", "")
        self.loc = location_id or os.environ.get("KENJI_LOCATION_ID", "")
        self._user = user_id or os.environ.get("KENJI_USER_ID") or None
        if not self.key or not self.loc:
            raise SystemExit("Set KENJI_API_KEY and KENJI_LOCATION_ID in your .env file (see README, Step 3).")
        self.h = {"Authorization": f"Bearer {self.key}", "Version": "2021-07-28", "Accept": "application/json"}

    def _check(self, r, what):
        if r.status_code >= 400:
            hint = " Check that your key has this permission turned on." if r.status_code in (401, 403) else ""
            raise SystemExit(f"Kenji {what} failed: {r.status_code} {r.text[:200]}{hint}")
        return r.json()

    def accounts(self):
        """Social accounts connected in Kenji's Social Planner."""
        r = requests.get(f"{BASE}/social-media-posting/{self.loc}/accounts", headers=self.h, timeout=30)
        accs = self._check(r, "list accounts").get("results", {}).get("accounts", [])
        return [a for a in accs if not a.get("isExpired")]

    def user_id(self):
        if not self._user:
            r = requests.get(f"{BASE}/users/", headers=self.h, params={"locationId": self.loc}, timeout=30)
            users = self._check(r, "find a user").get("users", [])
            if not users:
                raise SystemExit("No users on this Kenji account. Set KENJI_USER_ID in .env.")
            self._user = users[0]["id"]
        return self._user

    def upload(self, path):
        """Upload a video to the Kenji media library and return its public URL."""
        with open(path, "rb") as f:
            r = requests.post(f"{BASE}/medias/upload-file", headers=self.h,
                              files={"file": (os.path.basename(path), f, "video/mp4")},
                              data={"hosted": "false", "locationId": self.loc}, timeout=900)
        url = self._check(r, "media upload").get("url")
        if not url:
            raise SystemExit(f"Kenji media upload returned no URL: {r.text[:200]}")
        return url

    def post(self, video_url, caption, accounts, schedule_iso=None, youtube_title=None):
        """One Social Planner post per platform group. YouTube gets Shorts details."""
        base = {"type": "post", "userId": self.user_id(), "summary": caption,
                "media": [{"url": video_url, "type": "video/mp4"}]}
        if schedule_iso:
            base.update(status="scheduled", scheduleDate=schedule_iso)
        yt = [a["id"] for a in accounts if a.get("platform") == "youtube"]
        rest = [a["id"] for a in accounts if a.get("platform") != "youtube"]
        results = []
        hj = {**self.h, "Content-Type": "application/json"}
        if rest:
            r = requests.post(f"{BASE}/social-media-posting/{self.loc}/posts", headers=hj,
                              json={**base, "accountIds": rest}, timeout=120)
            results.append(("account(s) on Facebook / Instagram / TikTok / LinkedIn / Pinterest", len(rest), self._check(r, "create post")))
        if yt:
            title = (youtube_title or caption.split("\n")[0])[:95]
            r = requests.post(f"{BASE}/social-media-posting/{self.loc}/posts", headers=hj,
                              json={**base, "accountIds": yt,
                                    "youtubePostDetails": [{"title": title, "type": "short", "privacyLevel": "public"}]},
                              timeout=120)
            results.append(("YouTube channel(s) as a Short", len(yt), self._check(r, "create YouTube post")))
        return results
