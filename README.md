# 통합 업무 포털 (biz-portal)

경영 대시보드와 HR 챗봇을 단일 IP로 서비스하는 면접용 포트폴리오 사이트입니다.
**모든 데이터는 가상의 데모 데이터입니다.**

🔗 라이브: http://34.83.67.147

## 구성

```
사용자 → Nginx (GCP VM, 80포트)
          ├─ /            랜딩 페이지 (이 저장소)
          ├─ /dashboard/  경영 현황 종합 대시보드 (이 저장소, 정적)
          ├─ /chatbot/    HR 챗봇 → 127.0.0.1:8000 프록시 (별도 저장소: hr-chatbot)
          └─ /api/, /static/  챗봇 API·리소스 프록시
```

- **랜딩 페이지** (`index.html`) — 📊 경영 대시보드 / 💬 HR 챗봇 진입 버튼
- **경영 대시보드** (`dashboard/`) — 노션 "경영 현황 종합 대시보드"를 웹으로 구현
  - `index.html` 종합 현황: KPI·의사결정 안건·핵심 지표 차트·프로젝트 현황
  - `finance.html` 재무: 매출·비용 추이, 고정비/변동비, 현금흐름 예측
  - `people.html` 인력·조직: 부서별 인원·인건비, 입퇴사 현황
  - `recruiting.html` 채용: 칸반 파이프라인, 후보자·포지션 관리
- **기술**: 순수 HTML/CSS/JS + Chart.js(로컬 번들), 외부 CDN 의존 없음, 다크모드 지원
- **데이터**: 노션에서 받아 `dashboard/assets/data.js`로 생성 (아래 파이프라인)

## 데이터 파이프라인

`data.js`는 **생성물**입니다. 직접 고치지 말고 노션을 고친 뒤 다시 만듭니다.

```
노션 12개 DB ──fetch──▶ data/notion-raw.json ──normalize──▶ data/source.json
                                                                  │
                          data/manual.json ────────────────────────┤
                       (의사결정·현금흐름 예측 등 DB 밖의 값)        │
                                                              verify ─▶ build
                                                                         │
                                                        dashboard/assets/data.js
```

```bash
python3 tools/sync.py            # 정규화 → 검증 → 생성
python3 tools/sync.py --fetch    # 노션에서 새로 받아온 뒤 재생성 (NOTION_TOKEN 필요)
python3 tools/sync.py --strict   # 경고가 있어도 중단
bash tools/deploy.sh             # 검증 통과 시에만 VM 배포
```

Claude Code에서는 `/sync-dashboard` 로 수집부터 배포까지 한 번에 진행할 수 있습니다
(토큰 없이 노션 MCP 사용, 단 워크스페이스 요금제에 따라 쿼리 한도 있음).

| 파일 | 역할 |
|---|---|
| `tools/config.py` | 노션 DB 목록·부서→직군·파생 규칙 (여기만 고치면 됨) |
| `tools/fetch_notion.py` | 노션 공식 API 수집 (`NOTION_TOKEN` 필요) |
| `tools/normalize.py` | 노션 원본 → 월 배열 기준 정규화 |
| `tools/verify.py` | 정합성 검증 — 오류는 배포 차단, 경고는 보고 |
| `tools/build.py` | `data.js` 생성 |
| `data/manual.json` | 노션 DB에 없는 값(의사결정 안건·현금흐름 예측)만 사람이 관리 |

### 단일 진실 공급원

노션 DB끼리 값이 어긋날 때 무엇을 믿을지 `tools/config.py`에 못박아 두고, 어긋난
지점은 `verify.py`가 전부 보고합니다.

| 항목 | 출처 |
|---|---|
| 매출·현금 잔고·총원·입퇴사 | 📈 경영 핵심 지표 DB |
| 총비용 | 🏭 제조원가 DB의 제조원가 + 판관비 |
| 영업이익·이익률 | 매출 − 총비용 에서 파생 |
| 전사 인건비 | 제조원가 DB 노무비 + 부서별 사무직 인건비 |
| 고정비·변동비 | 🧾 월별 비용 구조 DB |

## 배포 (GCP VM)

```bash
bash tools/deploy.sh
```

`~/.config/gcloud`의 `portfolio` 구성(whlee79 계정)을 사용합니다. 최초 1회 Nginx 설정:

```bash
sudo cp deploy/portfolio.nginx.conf /etc/nginx/sites-available/portfolio
sudo ln -sf /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/portfolio
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

모든 응답에 `Cache-Control: no-cache`를 적용해 배포 즉시 반영됩니다.
