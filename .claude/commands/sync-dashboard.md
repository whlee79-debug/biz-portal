---
description: 노션 '경영 현황 종합 대시보드'를 읽어 대시보드 데이터를 재생성하고 배포합니다
allowed-tools: Bash, Read, Write, Edit
---

노션을 원본으로 삼아 `dashboard/assets/data.js` 를 다시 만듭니다.

## 절차

1. **수집** — `NOTION_TOKEN` 이 설정돼 있으면 API 경로가 빠릅니다.

   ```bash
   python3 tools/fetch_notion.py
   ```

   토큰이 없으면 노션 MCP로 받습니다. `tools/config.py` 의 `NOTION_DBS` 에 있는 DB를
   전부 조회해 `data/notion-raw.json` 을 같은 형식으로 다시 씁니다.
   - 각 DB는 `notion-query-data-sources` 로 `SELECT *` 합니다.
   - `positions` DB 행에는 페이지 id를 `_id` 로 함께 담습니다(후보자 관계 해석용).
   - `fetchedAt` 은 실행 시각(KST), `source` 는 `"mcp"` 로 적습니다.
   - MCP 쿼리 한도에 걸리면 그 DB는 `rows: []` 와 `unavailable` 사유를 남기고 계속
     진행합니다 — 비고성 DB는 `data/manual.json` 폴백이 있습니다.

2. **재생성** — 정규화 → 검증 → 생성을 한 번에 돌립니다.

   ```bash
   python3 tools/sync.py
   ```

3. **검증 결과 보고** — `[오류]` 는 배포를 막습니다. `[경고]` 는 노션 DB끼리 어긋난
   지점이므로, **어느 DB의 어느 행을 고쳐야 하는지** 사용자에게 그대로 전달합니다.
   경고를 임의로 무시하거나 숫자를 손으로 맞추지 마세요 — 노션을 고치는 게 원칙입니다.

4. **차이 확인** — 배포 전에 무엇이 바뀌는지 보여줍니다.

   ```bash
   git -C . diff --stat dashboard/assets/data.js
   ```

5. **배포** — 사용자가 승인하면 실행합니다. 승인 없이 배포하지 마세요.

   ```bash
   bash tools/deploy.sh
   ```

6. **확인** — 배포 후 http://34.83.67.147/dashboard/ 를 열어 KPI 숫자가 노션과
   맞는지 눈으로 확인하고, 결과를 요약해 보고합니다.

## 원칙

- `dashboard/assets/data.js` 는 생성물입니다. 직접 편집하지 마세요.
- 노션 DB에 없는 값(의사결정 안건·현금흐름 예측)만 `data/manual.json` 에서 관리합니다.
- 파생 규칙(총비용·영업이익·이익률·전사 인건비)은 `tools/config.py` 에 정리돼 있습니다.
  규칙을 바꿔야 하면 그 파일을 고치고, 생성 코드에 예외를 넣지 마세요.
