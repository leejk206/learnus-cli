import json
import re

import requests
from bs4 import BeautifulSoup
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

LEARNUS_BASE = "https://ys.learnus.org"
LOGIN_URL = f"{LEARNUS_BASE}/login.php"
SP_LOGIN_URL = f"{LEARNUS_BASE}/passni/sso/spLogin2.php"
PMSSO_SERVICE = "https://infra.yonsei.ac.kr/sso/PmSSOService"
PMSSO_AUTH = "https://infra.yonsei.ac.kr/sso/PmSSOAuthService"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}


class LoginError(Exception):
    """로그인 실패."""


def login(user_id: str, password: str) -> requests.Session:
    if not user_id or not password:
        raise LoginError("자격증명 오류: ID/PW가 비어 있음")

    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)

    try:
        session.get(LOGIN_URL, timeout=15)

        r_sp = session.get(SP_LOGIN_URL, headers={"Referer": LOGIN_URL}, timeout=15)
        r_sp.encoding = "euc-kr"
        frm_sso = BeautifulSoup(r_sp.text, "lxml").find("form", id="frmSSO")
        if frm_sso is None:
            raise LoginError("예상치 못한 응답: spLogin2에서 frmSSO 없음")
        sp_payload = {
            inp.get("name"): inp.get("value", "") for inp in frm_sso.find_all("input")
        }

        r_login = session.post(
            PMSSO_SERVICE,
            data=sp_payload,
            headers={"Referer": SP_LOGIN_URL},
            timeout=15,
        )

        sso_form = BeautifulSoup(r_login.text, "lxml").find("form", id="ssoLoginForm")
        if sso_form is None:
            raise LoginError("예상치 못한 응답: ssoLoginForm 없음")
        auth_payload = {
            inp.get("name"): inp.get("value", "") for inp in sso_form.find_all("input")
        }

        challenge_m = re.search(r"var\s+ssoChallenge\s*=\s*'([^']+)'", r_login.text)
        rsa_m = re.search(
            r"rsa\.setPublic\(\s*'([0-9a-fA-F]+)'\s*,\s*'([0-9a-fA-F]+)'\s*\)",
            r_login.text,
        )
        if not challenge_m or not rsa_m:
            raise LoginError("예상치 못한 응답: ssoChallenge 또는 RSA 키 추출 실패")

        sso_challenge = challenge_m.group(1)
        modulus_hex = rsa_m.group(1)
        exponent_hex = rsa_m.group(2)

        plain = json.dumps(
            {"userid": user_id, "userpw": password, "ssoChallenge": sso_challenge},
            separators=(",", ":"),
        )
        auth_payload["E2"] = _rsa_encrypt(plain, modulus_hex, exponent_hex)

        r_auth = session.post(
            PMSSO_AUTH,
            data=auth_payload,
            headers={"Referer": PMSSO_SERVICE},
            timeout=15,
        )

        _follow_autosubmit_forms(session, r_auth)

        dashboard = session.get(LEARNUS_BASE + "/", timeout=15)
    except requests.RequestException as e:
        raise LoginError(f"네트워크 오류: {e}") from e

    if not _is_logged_in(dashboard.text):
        raise LoginError("자격증명 오류: 로그인 후 대시보드 접근 실패")

    return session


def _rsa_encrypt(plaintext: str, modulus_hex: str, exponent_hex: str) -> str:
    n = int(modulus_hex, 16)
    e = int(exponent_hex, 16)
    pub = RSAPublicNumbers(e, n).public_key(default_backend())
    ct = pub.encrypt(plaintext.encode("utf-8"), PKCS1v15())
    return ct.hex()


def _follow_autosubmit_forms(session: requests.Session, response: requests.Response,
                              max_hops: int = 5) -> requests.Response:
    current = response
    for _ in range(max_hops):
        text = current.text
        soup = BeautifulSoup(text, "lxml")
        form = soup.find("form")
        if form is None:
            return current
        onload = (soup.body or {}).get("onload", "") if soup.body else ""
        has_autosubmit = (
            ".submit()" in text
            and ("onload" in text.lower())
            and form.get("action")
        )
        if not has_autosubmit:
            return current
        action = form.get("action")
        if not action.startswith("http"):
            from urllib.parse import urljoin
            action = urljoin(current.url, action)
        payload = {
            inp.get("name"): inp.get("value", "")
            for inp in form.find_all("input")
            if inp.get("name")
        }
        method = (form.get("method") or "post").lower()
        if method == "post":
            current = session.post(action, data=payload,
                                   headers={"Referer": current.url}, timeout=15)
        else:
            current = session.get(action, params=payload,
                                  headers={"Referer": current.url}, timeout=15)
    return current


def _is_logged_in(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    if soup.find("a", href=lambda h: h and "logout" in h):
        return True
    if "로그아웃" in html:
        return True
    return False
