# -*- coding: utf-8 -*-
"""동기화 — 정규화 → 검증 → 생성을 한 번에 실행합니다.

    python3 tools/sync.py             # 노션 원본(data/notion-raw.json) 기준으로 재생성
    python3 tools/sync.py --fetch     # 노션에서 새로 받아온 뒤 재생성 (NOTION_TOKEN 필요)
    python3 tools/sync.py --strict    # 경고가 있어도 생성 중단

노션 수집은 두 갈래입니다.
  1) NOTION_TOKEN 이 있으면 --fetch 로 공식 API에서 직접 받습니다(자동화용).
  2) 토큰 없이 쓸 때는 Claude Code에서 `/sync-dashboard` 를 실행하면
     노션 MCP로 받아 data/notion-raw.json 을 갱신한 뒤 이 스크립트를 부릅니다.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")


def run(script, args=()):
    print("\n── %s ──" % script)
    result = subprocess.run([sys.executable, os.path.join(TOOLS, script)] + list(args))
    return result.returncode


def main():
    strict = "--strict" in sys.argv

    if "--fetch" in sys.argv:
        if run("fetch_notion.py") != 0:
            print("\n수집 실패 — 중단합니다.")
            return 1

    if run("normalize.py") != 0:
        return 1

    code = run("verify.py", ["--strict"] if strict else [])
    if code != 0:
        print("\n검증에서 막혔습니다. 위 항목을 노션에서 고친 뒤 다시 실행하세요.")
        return code

    if run("build.py") != 0:
        return 1

    print("\n완료. 배포하려면: bash tools/deploy.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
