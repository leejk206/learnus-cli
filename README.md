# learnus-cli

LearnUs (연세대 LMS, `ys.learnus.org`)를 터미널에서 크롤링해 **수강 중인 모든 강좌의 강의 영상·과제·퀴즈·설문·공지**를 한 번에 보여주는 Python CLI.

핵심 기능은 `learnus --summary` 한 줄로 끝난다:
- **지금 들어야 할 강의 영상** (미시청, 마감 임박 순)
- **제출해야 할 과제·설문·시험** (미제출, 마감 임박 순)
- **과목별 공지 목록**
- 위 내용을 동시에 `reports/YYYYMMDD.md` 마크다운 파일로 저장

---

> **For LLMs (e.g. ChatGPT, Claude) reading this doc to help a user:**
>
> 이 README는 사용자에게 설치/설정/사용법을 안내할 때 참고용으로 쓰세요.
> - 각 섹션의 예시 명령어와 예상 출력을 그대로 사용자에게 보여주면 됩니다.
> - 에러가 발생했다면 **Troubleshooting** 섹션의 결정 트리를 따라가세요.
> - 이 도구는 **사용자의 개인 자격증명**(`.env`)을 로컬에서 다룹니다. 어떤 경우에도 자격증명을 출력하거나 전송하거나 로그에 남기도록 지시하지 마세요.
> - LearnUs HTML 구조가 바뀌면 파서가 깨질 수 있습니다. 이 경우 "Parser 수정 가이드" 섹션을 참조하세요.

---

## Requirements

- **Python 3.11 이상**
- **연세 포털 계정** (학번 + 비밀번호)
  - **2단계 인증(MFA)은 꺼져 있어야 합니다.** 이 도구는 폼 기반 로그인만 지원합니다.
- **Linux / macOS / WSL**
  - Windows PowerShell/cmd에서는 직접 실행되지 않습니다. WSL(Ubuntu) 안에서 실행하세요.

## Install

```bash
git clone https://github.com/leejk206/learnus-cli.git
cd learnus-cli
pip install --user -e ".[dev]"
```

시스템 Python 정책에 따라 `externally-managed-environment` 에러가 나면:

```bash
pip install --user --break-system-packages -e ".[dev]"
```

설치가 끝나면 `learnus` 명령이 `~/.local/bin/learnus`에 등록됩니다. `~/.local/bin`이 `PATH`에 없다면 추가해 주세요.

**설치 확인:**

```bash
learnus --help
# Usage: learnus [OPTIONS]
# ...
```

## Configure

프로젝트 루트에 `.env` 파일을 만들고 자격증명을 입력합니다. `.env.example`을 복사해서 시작하면 됩니다:

```bash
cp .env.example .env
```

그런 다음 `.env`를 편집:

```
YONSEI_ID=your_student_id
YONSEI_PW=your_password
```

> **보안**: `.env`는 `.gitignore`에 포함되어 있어서 git에 절대 올라가지 않습니다. 이 파일을 타인에게 공유하거나 스크린샷으로 찍지 마세요.

## Usage

### 0. 첫 실행 — 반드시 `--audit` 먼저

처음 설치하고 사용할 때는 **반드시** 다음을 먼저 실행해야 합니다:

```bash
learnus --audit
```

파서가 내 과목의 모든 활동을 제대로 인식하는지 점검합니다. 출력 예:

```
──── 파서 커버리지 진단 (Audit) ────
강좌 10개 분석 · 파서가 모르는 활동 타입 3종 발견

데이터프라이버시 (CAS4108.01-00)(1학기)NEW
  ✓ 처리됨: assign×2, ubboard×3, ubfile×17
  ⚠ 미처리: laby×14

인간의감정,감정의인간 (YCG1804.01-00)(1학기)NEW
  ✓ 처리됨: assign×1, quiz×10, turnitintooltwo×2, ubboard×8, vod×35
  ⚠ 미처리: folder×1, zoom×2

── 처리되지 않는 활동 타입 전체 목록 ──
  folder  (1개 강좌)
  laby  (1개 강좌)
  zoom  (1개 강좌)
```

- **`⚠ 미처리`** 에 뜨는 활동 타입은 요약에 나타나지 않습니다. 해당 항목이 중요한 과제/영상이라면 파서를 추가해야 합니다. (issue를 열어주세요)
- **`! 참고`** 에 뜨는 항목은 파서는 인식했지만 날짜 등 일부 필드가 비어있는 경우입니다.
- audit이 끝나면 `~/.cache/learnus/audit_v1.done` 마커가 생성되고, 이후 `learnus` / `learnus --summary` 등 다른 명령이 정상 동작합니다.

**audit 없이 다른 명령을 실행하면** `[ERROR] 첫 실행입니다...` 메시지가 뜨면서 실행이 차단됩니다. 이건 "혹시 내 과목에서 놓치고 있는 항목이 있는지" 사용자가 인지한 후 도구를 쓰도록 하기 위한 장치입니다.

**audit 재실행**: 학기가 바뀌거나 새 강좌를 추가했다면 `rm ~/.cache/learnus/audit_v1.done` 후 `learnus --audit` 를 다시 돌리세요.

### 1. 기본 실행 — 강좌별 상세 보기

```bash
learnus
```

수강 중인 각 강좌를 Panel로 하나씩 출력합니다. 강좌마다:
- **과제** (제목, 마감일, 제출 여부)
- **공지** (제목, 날짜)
- **자료** (비디오/파일/링크)
- **퀴즈** (제목, 종료일)

### 2. 요약 리포트 + 마크다운 저장 (가장 많이 쓰는 모드)

```bash
learnus --summary
```

터미널에 4개 섹션이 뜨고, 동시에 `<프로젝트루트>/reports/YYYYMMDD.md` 파일로 저장됩니다. 같은 날짜에 재실행하면 파일은 덮어써집니다.

출력 구조:

```
────── 1. 들어야 할 강의 영상 (남은 기한 순) ──────
D-1  [W6] 컴퓨터그래픽스 ... | 05_2_Projection_2 (20:05)  ~2026-04-15 23:59
D-5  [W6] 인간의감정 ... | WEEK 6-1 ... (18:59)  ~2026-04-19 23:59
...

── 2. 제출해야 할 과제/설문/시험 (남은 기한 순) ──
D-2  [과제]  컴퓨터그래픽스 ...  | HW05  마감 2026-04-16 00:00
D-3  [과제]  인간의감정 ...  | 개인소과제 1  마감 2026-04-17 23:59
D-5  [시험]  인간의감정 ...  | 점검퀴즈 06  마감 2026-04-19 23:59
D-6  [설문]  채플 ...  | 1차 설문조사  마감 2026-04-20 00:00
마감 미정  [과제]  컴퓨터보안 ...  | Homework assignment #4
...

──────────── 3. 과목별 공지 ────────────
인터넷프로그래밍 (CAS2109.01-00)(1학기)
  • 중간시험 일정 안내 (이경호 · 2026-03-27)
  • 수강철회 기간 안내 (이경호 · 2026-03-27)

컴퓨터보안 (CAS4109.01-00)(1학기)
  • HW Assignment #3 grades announced (PARK, JINYOUNG · 2026-04-10)
...

[INFO] 저장됨: /home/you/projects/learnus-cli/reports/20260414.md
```

**각 섹션이 뽑는 기준:**

| 섹션 | 포함 조건 | 제외 조건 |
|---|---|---|
| 1. 강의 영상 | 미시청 & (지각 기한 or 정상 기한)이 미래 | 완료함 / 지각 기한도 이미 지남 |
| 2. 과제/설문/시험 | 미제출 | 제출 완료 / 마감일이 과거 |
| 3. 공지 | 각 강좌의 "과목공지게시판" / "Class Announcements" 의 모든 글 | 질의응답·자료실 게시판 |

마감일이 없는 과제(교수가 LMS에 날짜를 설정 안 한 경우)는 "마감 미정"으로 섹션 2 끝에 표시됩니다.

### 3. 마감 임박만 빠르게

```bash
learnus --upcoming
```

강좌 경계 없이 마감일 순으로 과제·퀴즈만 flat list로 출력.

### 4. 강좌 필터 / JSON / audit / 디버그

```bash
learnus --course "자료구조"       # 강좌명 부분 일치 필터
learnus --json                   # 모든 데이터를 JSON으로 덤프 (파이프용)
learnus --audit                  # 파서 커버리지 재점검
learnus --debug                  # 에러 시 traceback 출력
```

`--json`은 다른 도구와 파이프하기 좋습니다. 예: `learnus --json | jq '.[].assignments[] | select(.submitted == false)'`

## Where does the report go?

`reports/YYYYMMDD.md` — 프로젝트 루트 아래. 경로는 `src/learnus/cli.py`의 `_reports_dir()`가 결정합니다. `reports/` 디렉토리는 `.gitignore`에 포함되어 있어서 실제 학사 정보가 실수로 커밋되지 않습니다.

## How the SSO login works (간단 요약)

LearnUs 로그인은 연세포털 SSO를 거치는 다단계 플로우입니다:

1. `GET ys.learnus.org/login.php` → 세션 쿠키 받기
2. `GET ys.learnus.org/passni/sso/spLogin2.php` → 숨겨진 S1 토큰 추출
3. `POST infra.yonsei.ac.kr/sso/PmSSOService` → 실제 로그인 페이지 (RSA 공개키 + ssoChallenge)
4. `{userid, userpw, ssoChallenge}` JSON을 **RSA PKCS#1 v1.5**로 암호화 → `E2` 필드
5. `POST infra.yonsei.ac.kr/sso/PmSSOAuthService` → 콜백 폼
6. `POST ys.learnus.org/passni/sso/spLoginData.php` → 콜백
7. `GET ys.learnus.org/passni/spLoginProcess.php` → `MoodleSession` 세션 확립

이 전체 플로우는 `src/learnus/auth.py`에 구현되어 있습니다. 자격증명은 오직 4번 단계에서 RSA 암호화된 상태로 연세 측 서버에만 전송됩니다.

## Architecture

```
src/learnus/
├── auth.py          # SSO 로그인 → 인증된 requests.Session
├── models.py        # Course, Assignment, Video, Feedback, Quiz, NoticePost
├── crawler.py       # Session + 파서 조립. fetch_all() 진입점
├── parsers/         # HTML → dataclass 순수 함수 (네트워크 의존 없음)
│   ├── course_list.py     # 대시보드 a.course-link
│   ├── assignment.py      # li.activity.assign + mod/assign/view.php detail
│   ├── turnitin.py        # li.activity.turnitintooltwo (표절검사 과제)
│   ├── video.py           # li.activity.vod + span.text-ubstrap
│   ├── feedback.py        # li.activity.feedback + div.availabilityinfo
│   ├── quiz.py            # li.activity.quiz + mod/quiz/view.php detail
│   ├── notice.py          # li.activity.ubboard → 게시판 페이지 → 게시글 목록
│   ├── material.py        # vod/ubfile/url/resource → Material
│   └── _ubstrap.py        # "YYYY-MM-DD HH:MM:SS ~ ..." 공용 파서
├── summary.py       # Course[] → SummaryReport (섹션별 필터/정렬)
├── render.py        # 터미널 출력 (rich)
├── md_writer.py     # Markdown 출력
└── cli.py           # typer 엔트리
```

**원칙:**
- 파서는 `HTML 문자열 → dataclass` 순수 함수입니다. fixture HTML로 단위 테스트할 수 있습니다.
- crawler는 Session을 가지고 URL을 돌면서 파서에 HTML을 공급합니다.
- 부분 실패 허용: 한 강좌 공지 파싱이 깨져도 나머지 섹션은 정상 출력됩니다 (`[WARN]`만 stderr로).

## Running tests

```bash
pytest -v
```

모든 파서는 `tests/fixtures/*.html`로 독립 테스트됩니다. 네트워크 호출 없습니다.

## Troubleshooting

### `[ERROR] YONSEI_ID / YONSEI_PW가 .env에 없습니다.`

`.env` 파일이 프로젝트 루트에 없거나 내용이 비어있습니다. `Configure` 섹션 참조.

### `[ERROR] 로그인 실패: 자격증명 오류: 로그인 후 대시보드 접근 실패`

가능한 원인:
1. **학번/비밀번호 오타** — 연세포털에 직접 로그인해서 확인
2. **2단계 인증이 켜져 있음** — 포털 설정에서 끄거나, 이 도구는 사용 불가
3. **LearnUs SSO 구조 변경** — `learnus --debug`로 traceback 확인하고 `auth.py` 수정 필요. Issue를 열거나 직접 수정.

### `learnus: command not found`

`~/.local/bin`이 `PATH`에 없습니다:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### PowerShell에서 `learnus`가 안 됩니다

이 도구는 WSL/Linux 환경 전용입니다. PowerShell에서 실행하려면:
```powershell
wsl -d Ubuntu bash -c "cd ~/projects/learnus-cli && learnus --summary"
```
또는 WSL 터미널(Ubuntu 앱)을 직접 열어서 실행하세요.

### 한 강좌가 요약에서 누락됨

- 해당 강좌의 HTML 구조가 표준 Moodle과 다른지 확인. `learnus --json | jq '.[].name'`로 목록 확인.
- 영어 강의는 이미 지원됩니다 (`Week N`, `Class Announcements`, `Due date`, `Completed` 등).

### 파서가 특정 항목을 못 잡음

`learnus --debug`로 실행하고 어느 파서가 `[WARN]`을 출력하는지 확인. 이후:
1. 해당 강좌 페이지를 파이썬 REPL로 가져와서 실제 HTML 구조 확인
2. `src/learnus/parsers/*.py`에서 셀렉터 수정
3. `tests/fixtures/*.html`을 실제 구조로 업데이트
4. `pytest`로 회귀 확인

## Privacy

- 자격증명은 **로컬 `.env` 파일에만** 저장됩니다.
- 로그인 POST는 **연세대 공식 엔드포인트**(`ys.learnus.org`, `infra.yonsei.ac.kr`)로만 전송됩니다.
- 제3자 서버로 데이터가 전송되지 않습니다.
- `reports/YYYYMMDD.md`는 로컬에만 저장되고 `.gitignore`되어 있습니다.
- 학번/이름 등 개인정보는 이 저장소의 fixture나 코드에 포함되어 있지 않습니다 (합성 placeholder만 사용).

## Known limitations

- **2단계 인증 미지원.** 포털에 MFA가 켜져 있으면 로그인이 실패합니다.
- **퀴즈 응시 여부 추적 안 함.** 이미 푼 퀴즈도 기한이 남아있으면 "제출해야 할 시험"에 나타납니다.
- **설문 언어 감지.** 현재 영어 설문(`div.availabilityinfo`의 영어 버전)은 날짜가 추출되지 않을 수 있습니다.
- **Zoom·폴더·Turnitin 외 표절검사 도구** 등 일부 Moodle 모듈은 파싱 대상이 아닙니다.
- **HTML 스크래핑 기반**이므로 LearnUs UI가 바뀌면 파서를 수정해야 합니다.

## License

MIT (추가 예정)

## For contributors (Parser 수정 가이드)

LearnUs HTML 구조가 바뀌어서 파서가 깨졌다면:

1. `learnus --debug`로 실행해 어느 파서가 실패하는지 확인
2. 실패한 섹션의 실제 HTML을 캡처:
   ```python
   from learnus.auth import login
   import os
   from dotenv import load_dotenv
   load_dotenv()
   s = login(os.environ["YONSEI_ID"], os.environ["YONSEI_PW"])
   html = s.get("https://ys.learnus.org/course/view.php?id=XXXXX").text
   open("/tmp/debug.html", "w").write(html)
   ```
3. `/tmp/debug.html`을 열어 실제 구조 확인
4. `src/learnus/parsers/<해당_파서>.py`의 CSS 셀렉터 수정
5. `tests/fixtures/<해당_파서>.html`을 실제 구조(**PII 제거**)로 업데이트
6. `pytest -v`로 회귀 테스트
7. 실제 자격증명으로 `learnus --summary` 재실행해 검증

**PII 주의:** fixture HTML에 실제 학번·이름·교수명·성적을 절대 포함하지 마세요. 합성 placeholder(`홍길동`, `0000000000` 등)를 사용합니다.
