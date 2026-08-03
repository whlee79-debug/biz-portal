# -*- coding: utf-8 -*-
"""수집 — 노션 공식 API에서 DB 행을 받아 data/notion-raw.json 을 만듭니다.

    export NOTION_TOKEN=ntn_xxx
    python3 tools/fetch_notion.py

준비(최초 1회)
  1. https://www.notion.so/my-integrations 에서 내부 통합을 만들고 토큰을 복사합니다.
  2. 노션 '경영 현황 종합 대시보드'와 '2026 채용 대시보드' 페이지에서
     ⋯ → 연결 → 만든 통합을 추가합니다(하위 DB까지 함께 열립니다).

토큰이 없으면 Claude Code에서 `/sync-dashboard` 를 쓰세요 — 노션 MCP로 같은 파일을
만듭니다. 다만 MCP 쿼리는 워크스페이스 요금제에 따라 호출 한도가 있습니다.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import NOTION_DBS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "data", "notion-raw.json")
API = "https://api.notion.com/v1"
VERSION = "2022-06-28"

# 관계형 속성의 대상 페이지 id를 그대로 실어야 하는 DB(정규화 단계에서 이름으로 해석)
ID_COLUMN_DBS = {"positions"}


def request(path, payload, token):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API + path, data=body, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Notion-Version": VERSION,
        "Content-Type": "application/json",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429 and attempt < 3:          # 속도 제한 → 잠깐 쉬고 재시도
                time.sleep(2 ** attempt)
                continue
            if e.code == 404:
                raise SystemExit(
                    "노션이 %s 를 찾지 못했습니다. 통합이 해당 페이지에 연결됐는지 확인하세요.\n  %s"
                    % (path, detail))
            raise SystemExit("노션 API 오류 %d: %s" % (e.code, detail))
    raise SystemExit("노션 API 재시도 실패: " + path)


def plain(prop):
    """노션 속성 하나를 파이썬 값으로 폅니다."""
    kind = prop.get("type")
    value = prop.get(kind)

    if kind in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in value) or None
    if kind == "number":
        return value
    if kind in ("select", "status"):
        return value.get("name") if value else None
    if kind == "multi_select":
        return [v["name"] for v in value]
    if kind == "date":
        if not value:
            return None
        start = value.get("start")
        # 시각까지 있는 날짜만 UTC ISO로 넘깁니다(정규화 단계에서 KST로 변환).
        return start
    if kind == "checkbox":
        return value
    if kind == "relation":
        return [item["id"] for item in value]
    if kind == "people":
        return [p.get("name", "") for p in value]
    if kind == "formula":
        return plain({"type": value.get("type"), value.get("type"): value.get(value.get("type"))})
    if kind == "rollup":
        inner = value.get("type")
        if inner == "array":
            return [plain(v) for v in value.get("array", [])]
        return value.get(inner)
    return None


def fetch_db(key, meta, token):
    rows, cursor = [], None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        data = request("/databases/%s/query" % meta["id"], payload, token)
        for page in data["results"]:
            row = {name: plain(prop) for name, prop in page["properties"].items()}
            if key in ID_COLUMN_DBS:
                row["_id"] = page["id"]
            rows.append(row)
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return rows


def main():
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise SystemExit(
            "NOTION_TOKEN 이 없습니다.\n"
            "  export NOTION_TOKEN=ntn_xxx  후 다시 실행하거나,\n"
            "  Claude Code에서 `/sync-dashboard` 를 쓰세요(MCP 경로).")

    kst = timezone(timedelta(hours=9))
    out = {
        "fetchedAt": datetime.now(kst).isoformat(timespec="seconds"),
        "source": "notion-api",
        "note": "노션 원본 스냅샷. tools/fetch_notion.py 가 생성합니다. 직접 수정하지 마세요.",
        "databases": {},
    }

    for key, meta in NOTION_DBS.items():
        rows = fetch_db(key, meta, token)
        out["databases"][key] = {"id": meta["id"], "title": meta["title"], "rows": rows}
        print("  %-14s %-22s %3d행" % (key, meta["title"], len(rows)))

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("수집 완료: data/notion-raw.json (DB %d개)" % len(out["databases"]))


if __name__ == "__main__":
    main()
