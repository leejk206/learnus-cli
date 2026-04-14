import json
import os
import re

import requests
from bs4 import BeautifulSoup
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
uid = os.getenv("YONSEI_ID", "")
pw = os.getenv("YONSEI_PW", "")

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
})

s.get("https://ys.learnus.org/login.php", timeout=15)
r2 = s.get("https://ys.learnus.org/passni/sso/spLogin2.php",
           headers={"Referer": "https://ys.learnus.org/login.php"}, timeout=15)
r2.encoding = "euc-kr"
frm = BeautifulSoup(r2.text, "lxml").find("form", id="frmSSO")
sp_payload = {inp.get("name"): inp.get("value", "") for inp in frm.find_all("input")}

r3 = s.post("https://infra.yonsei.ac.kr/sso/PmSSOService", data=sp_payload,
            headers={"Referer": "https://ys.learnus.org/passni/sso/spLogin2.php"}, timeout=15)

sso_form = BeautifulSoup(r3.text, "lxml").find("form", id="ssoLoginForm")
auth_payload = {inp.get("name"): inp.get("value", "") for inp in sso_form.find_all("input")}

ch = re.search(r"var\s+ssoChallenge\s*=\s*'([^']+)'", r3.text)
rsa_m = re.search(r"rsa\.setPublic\(\s*'([0-9a-fA-F]+)'\s*,\s*'([0-9a-fA-F]+)'\s*\)", r3.text)
plain = json.dumps({"userid": uid, "userpw": pw, "ssoChallenge": ch.group(1)}, separators=(",", ":"))
n = int(rsa_m.group(1), 16)
e = int(rsa_m.group(2), 16)
pub = RSAPublicNumbers(e, n).public_key(default_backend())
auth_payload["E2"] = pub.encrypt(plain.encode("utf-8"), PKCS1v15()).hex()

r4 = s.post("https://infra.yonsei.ac.kr/sso/PmSSOAuthService", data=auth_payload,
            headers={"Referer": "https://infra.yonsei.ac.kr/sso/PmSSOService"}, timeout=15)
print(f"STEP4: {r4.status_code}, url={r4.url}, len={len(r4.text)}")

# Follow the callback form (ssoLoginForm → spLoginData.php)
callback_form = BeautifulSoup(r4.text, "lxml").find("form", id="ssoLoginForm")
if callback_form is None:
    print("ERROR: no ssoLoginForm in callback response")
else:
    action = callback_form.get("action")
    callback_payload = {inp.get("name"): inp.get("value", "")
                        for inp in callback_form.find_all("input") if inp.get("name")}
    print(f"STEP5 posting to: {action}")
    print(f"  keys: {list(callback_payload.keys())}")
    r5 = s.post(action, data=callback_payload,
                headers={"Referer": r4.url}, timeout=15)
    print(f"STEP5: {r5.status_code}, url={r5.url}, len={len(r5.text)}")
    print(f"  cookies: {list(s.cookies.keys())}")

    # Check for more forms
    soup5 = BeautifulSoup(r5.text, "lxml")
    for i, f in enumerate(soup5.find_all("form")):
        print(f"  form {i}: id={f.get('id')}, action={f.get('action')}")

# Final dashboard
final = s.get("https://ys.learnus.org/", timeout=15)
print(f"\nFINAL: {final.status_code}, len={len(final.text)}")
print(f"  MoodleSession cookie: {s.cookies.get('MoodleSession')}")

# Real check: find logout anchor
fsoup = BeautifulSoup(final.text, "lxml")
logout_a = fsoup.find("a", href=lambda h: h and "logout" in h.lower())
print(f"  logout anchor: {logout_a.get('href') if logout_a else None}")

# Find user name display / course list
courseboxes = fsoup.select("div.coursebox")
print(f"  courseboxes: {len(courseboxes)}")

# Save for inspection
with open("/tmp/final_dashboard.html", "w", encoding="utf-8") as f:
    f.write(final.text)
print("  saved /tmp/final_dashboard.html")
