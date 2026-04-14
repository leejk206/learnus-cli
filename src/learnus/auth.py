import requests
from bs4 import BeautifulSoup

LEARNUS_BASE = "https://ys.learnus.org"
LOGIN_URL = f"{LEARNUS_BASE}/login.php"
SSO_LOGIN_URL = f"{LEARNUS_BASE}/passni/sso/coursemosLogin.php"


class LoginError(Exception):
    """로그인 실패. 메시지에 원인 포함:
    - '자격증명 오류'
    - '네트워크 오류'
    - '예상치 못한 응답'
    """


def login(user_id: str, password: str) -> requests.Session:
    if not user_id or not password:
        raise LoginError("자격증명 오류: ID/PW가 비어 있음")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; learnus-cli/0.1)",
    })

    try:
        session.get(LOGIN_URL, timeout=10)
        resp = session.post(
            SSO_LOGIN_URL,
            data={"username": user_id, "password": password},
            timeout=10,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        raise LoginError(f"네트워크 오류: {e}") from e

    if resp.status_code != 200:
        raise LoginError(f"예상치 못한 응답: HTTP {resp.status_code}")

    try:
        dashboard = session.get(LEARNUS_BASE + "/", timeout=10)
    except requests.RequestException as e:
        raise LoginError(f"네트워크 오류: {e}") from e

    if not _is_logged_in(dashboard.text):
        raise LoginError("자격증명 오류: 로그인 후 대시보드 접근 실패")

    return session


def _is_logged_in(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    if soup.find("a", href=lambda h: h and "logout" in h):
        return True
    if "로그아웃" in html:
        return True
    return False
