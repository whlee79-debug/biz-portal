# 통합 업무 포털 (biz-portal)

가상의 화장품 ODM·OEM 제조사 **주식회사 홍길동**(정직원 120명)의 경영 현황 대시보드와
HR 규정 챗봇을 한 사이트로 묶은 포트폴리오입니다.
**모든 회사·인물·수치는 가상의 데모 데이터입니다.**

🔗 **라이브: https://wonho98.duckdns.org**

| 화면 | 주소 |
|---|---|
| 포털 첫 화면 | `/` |
| 경영 현황 종합 대시보드 | [`/dashboard/`](https://wonho98.duckdns.org/dashboard/) |
| 재무·제조원가 | [`/dashboard/finance.html`](https://wonho98.duckdns.org/dashboard/finance.html) |
| 인력·조직 | [`/dashboard/people.html`](https://wonho98.duckdns.org/dashboard/people.html) |
| 채용 | [`/dashboard/recruiting.html`](https://wonho98.duckdns.org/dashboard/recruiting.html) |
| 채용 채널 분석 | [`/dashboard/pipeline.html`](https://wonho98.duckdns.org/dashboard/pipeline.html) |
| 인건비 시뮬레이터 | [`/dashboard/simulator.html`](https://wonho98.duckdns.org/dashboard/simulator.html) |
| HR 규정 챗봇 | [`/chatbot/`](https://wonho98.duckdns.org/chatbot/) · 코드는 [hr-chatbot](https://github.com/whlee79-debug/hr-chatbot) |

## 왜 만들었나

인사·경영지원 실무에서 매달 반복되는 "엑셀 취합 → 숫자 맞추기 → 보고서 작성"을
**원본 한 곳 + 자동 검증 + 자동 배포**로 바꿔 보는 것이 목표였습니다.

- 숫자는 한 곳(옵시디언 노트의 표)에서만 고칩니다.
- 표끼리 어긋나면(예: 고정비 + 변동비 ≠ 총비용) 배포 전에 검증 단계가 막고, 덜 치명적인 불일치(예: 월별 입사 합계 ≠ 채널별 채용 합계)는 경고로 보고합니다.
- 통과하면 스크립트 한 줄로 서버에 반영됩니다.

## 대시보드 구성

- **종합 현황** — 매출·영업이익·인원 KPI, 이번 달 의사결정 안건, 핵심 지표 추이, 주요 프로젝트
- **재무·제조원가** — 매출·비용 추이, 원료비·포장재·노무비·파견용역비, 고정비/변동비, 현금흐름 예측
- **인력·조직** — 부서별 인원·인건비, 입퇴사·이직률, 근태·안전, 정직원/파견 구성
- **채용** — 포지션별 진행 현황, 후보자 칸반, 채널별 채용 성과
- **채용 채널 분석 · 인건비 시뮬레이터** — "지원자 많은 채널 ≠ 좋은 채널", "연봉 총액 예산은 매년 모자란다"를 숫자로 보여주는 인터랙티브 페이지

**기술**: 순수 HTML/CSS/JavaScript + Chart.js(로컬 번들). 빌드 도구·프레임워크 없음.
기본은 라이트 테마이며 주소 끝에 `?theme=dark`를 붙이면 다크 테마로 볼 수 있습니다.

## 데이터 파이프라인

`dashboard/assets/data.js`는 **생성물**입니다. 직접 고치지 않고, 원본 노트를 고친 뒤 다시 만듭니다.

```
옵시디언 볼트 (BizPortal 노트 6개의 마크다운 표)
        │ fetch_obsidian.py
        ▼
data/notion-raw.json + data/manual.json      ← 교환 형식 (노션 시절 구조 유지)
        │ normalize.py
        ▼
data/source.json                              ← 월 배열 기준으로 정규화
        │ verify.py   (오류 = 배포 차단, 경고 = 보고)
        ▼
        │ build.py
        ▼
dashboard/assets/data.js
```

```bash
python3 tools/sync.py            # 수집 → 정규화 → 검증 → 생성
python3 tools/sync.py --strict   # 경고가 있어도 중단
bash tools/deploy.sh             # 검증 통과 시에만 서버 배포
```

| 파일 | 역할 |
|---|---|
| `tools/fetch_obsidian.py` | 볼트 노트의 표 → 교환 형식 JSON |
| `tools/config.py` | 부서→직군 매핑, 파생 규칙 (규칙을 바꿀 땐 여기만) |
| `tools/normalize.py` | 월 배열 기준 정규화 |
| `tools/verify.py` | 정합성 검증 |
| `tools/build.py` | `data.js` 생성 |
| `tools/deploy.sh` | GCP VM으로 정적 파일 업로드 |
| `tools/fetch_notion.py` | (이전) 노션이 원본이던 시절의 수집기 |

### 검증하는 것

어느 표를 기준으로 삼을지 `tools/config.py`에 못박아 두고, 어긋난 지점은 `verify.py`가 전부 보고합니다.

| 항목 | 기준 |
|---|---|
| 매출·현금 잔고·총원·입퇴사 | 경영 핵심 지표 표 |
| 총비용 | 제조원가 + 판관비 |
| 영업이익·이익률 | 매출 − 총비용에서 파생 |
| 전사 인건비 | 생산직 노무비(제조원가 표) + 사무직 인건비(부서별 인원 표) |
| 채용 | 월별 입사 합계 = 채널별 채용 합계 |
| 고정비·변동비 | 월별 비용 구조 표 (합계 ≠ 총비용이면 배포 차단) |

## 인프라

```
사용자 ─HTTPS─▶ Nginx (GCP e2-micro VM, Let's Encrypt)
                 ├─ /            포털 첫 화면 (이 저장소)
                 ├─ /dashboard/  경영 대시보드 (이 저장소, 정적)
                 ├─ /chatbot/    HR 챗봇 → FastAPI 127.0.0.1:8000 프록시
                 └─ /api/        챗봇 API (SSE 스트리밍, 버퍼링 끔)
```

- 도메인: DuckDNS 무료 도메인 + Let's Encrypt 인증서(자동 갱신)
- 캐시: 모든 응답에 `Cache-Control: no-cache` — 배포 즉시 반영
- 모니터링: n8n 워크플로가 10분마다 사이트 상태를 점검하고 장애 시 푸시·메일 알림
- Nginx 설정 원본: `deploy/portfolio.nginx.conf`

## 폴더

```
index.html          포털 첫 화면
dashboard/          대시보드 6개 화면 + assets(app.js, style.css, data.js, chart.js)
data/               파이프라인 중간 산출물
tools/              수집·정규화·검증·생성·배포 스크립트
deploy/             Nginx 설정
archive/            이전 컨셉(건설업) 시절의 원본 노트 보관
```
