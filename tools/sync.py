# -*- coding: utf-8 -*-
"""동기화 — 수집(옵시디언) → 정규화 → 검증 → 생성을 한 번에 실행합니다.

    python3 tools/sync.py             # 볼트 기준으로 재생성
    python3 tools/sync.py --strict    # 경고가 있어도 생성 중단

원본은 옵시디언 볼트(MyBrain/Personal/Portfolio/BizPortal)입니다.
볼트 노트의 표를 고친 뒤 이 스크립트를 실행하면 data.js까지 재생성됩니다.
배포는 `bash tools/deploy.sh`.

(과거에는 노션이 원본이었습니다 — 그 시절 수집기는 tools/fetch_notion.py로 남아 있습니다.)
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

    if run("fetch_obsidian.py") != 0:
        print("\n수집 실패 — 볼트 노트의 표 형식을 확인하세요.")
        return 1

    if run("normalize.py") != 0:
        return 1

    code = run("verify.py", ["--strict"] if strict else [])
    if code != 0:
        print("\n검증에서 막혔습니다. 위 항목을 옵시디언 볼트에서 고친 뒤 다시 실행하세요.")
        return code

    if run("build.py") != 0:
        return 1

    print("\n완료. 배포하려면: bash tools/deploy.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
