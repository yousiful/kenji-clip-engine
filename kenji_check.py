"""Check your Kenji connection: lists the social accounts your clips will go to. Sends nothing.

  python kenji_check.py
"""
from collections import Counter

from dotenv import load_dotenv

from clipper.kenji import Kenji

load_dotenv()
k = Kenji()
accounts = k.accounts()
print(f"Connected to Kenji. User for posts: {k.user_id()}")
if not accounts:
    print("No social accounts connected yet. Do README Step 2, then run this again.")
else:
    print(f"{len(accounts)} account(s) ready:")
    for a in accounts:
        print(f"   {a.get('platform', '?'):<10} {a.get('name', '')}")
    print("\nBy platform:", dict(Counter(a.get("platform") for a in accounts)))
