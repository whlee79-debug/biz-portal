# -*- coding: utf-8 -*-
"""수집(옵시디언) — BizPortal 볼트의 마크다운 표 → data/notion-raw.json + data/manual.json

옵시디언 볼트(MyBrain/Personal/Portfolio/BizPortal)가 유일한 원본입니다.
노트의 표를 파이프라인 교환 형식(notion-raw.json과 같은 구조)으로 변환해,
normalize → verify → build 단계를 그대로 재사용합니다.

    python3 tools/fetch_obsidian.py

노트 ↔ 데이터 매핑
    재무.md        월별 재무 현황 / 월별 비용 구조 / 월별 시공원가 / 현금흐름 예측
    인력·조직.md   월별 인력 현황 / 부서별 인원 / 월별 근태·안전 / 직군별 인건비 구성
    채용.md        후보자 파이프라인 / 채용 포지션 / 채널별 채용 성과
    프로젝트.md    주요 프로젝트·계약
    경영 요약.md   의사결정 요청 + frontmatter(기준월·보고월)
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta

VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
    "MyBrain/Personal/Portfolio/BizPortal")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "data", "notion-raw.json")
MANUAL_PATH = os.path.join(ROOT, "data", "manual.json")

KST = timedelta(hours=9)


def read_note(name):
    path = os.path.join(VAULT, name + ".md")
    if not os.path.exists(path):
        sys.exit("오류: 볼트에 '%s.md' 노트가 없습니다 (%s)" % (name, VAULT))
    with open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    props = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                props[k.strip()] = v.strip()
    return props


def coerce(cell):
    """표 셀 → 숫자/문자/None. '—'와 빈칸은 None."""
    s = cell.strip()
    if s in ("", "—", "-"):
        return None
    plain = s.replace(",", "")
    if re.fullmatch(r"-?\d+", plain):
        return int(plain)
    if re.fullmatch(r"-?\d+\.\d+", plain):
        return float(plain)
    return s


def table_after(text, heading, required=True):
    """'## heading'(부분 일치) 뒤에 나오는 첫 마크다운 표 → [dict]."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("#") and heading in line:
            start = i  # 같은 제목이 여럿이면(H1+H2) 마지막 것 — 표에 가장 가깝다
    if start is None:
        if required:
            sys.exit("오류: 제목 '%s'을(를) 찾지 못했습니다." % heading)
        return []
    header, rows = None, []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if header is not None and not stripped.startswith("|"):
            break  # 표 끝
        if not stripped.startswith("|"):
            if stripped.startswith("#"):  # 다음 섹션까지 표가 없음
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue  # 구분선
        row = {header[i]: coerce(cells[i]) for i in range(min(len(header), len(cells)))}
        rows.append(row)
    if required and not rows:
        sys.exit("오류: 제목 '%s' 아래에서 표를 찾지 못했습니다." % heading)
    return rows


def pseudo_id(name):
    """포지션명 → 32자리 hex 의사 id (노션 관계형 id 자리를 대신합니다)."""
    return hashlib.md5(("bizportal-position:" + name).encode("utf-8")).hexdigest()


def kst_to_utc_iso(value):
    """'2026-08-21 10:30'(KST) → '2026-08-21T01:30:00.000+00:00'(UTC)."""
    if not value or not isinstance(value, str):
        return None
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M") - KST
    return dt.strftime("%Y-%m-%dT%H:%M:00.000+00:00")


def month_korean(ym):
    """'2026-07' → ('2026년 7월', 7)."""
    y, m = ym.split("-")
    return "%s년 %d월" % (y, int(m)), int(m)


def main():
    finance = read_note("재무")
    people = read_note("인력·조직")
    recruit = read_note("채용")
    projects_note = read_note("프로젝트")
    summary = read_note("경영 요약")

    fin_rows = table_after(finance, "월별 재무 현황")
    cost_rows = table_after(finance, "월별 비용 구조")
    mfg_rows = table_after(finance, "월별 시공원가")
    forecast = table_after(finance, "현금흐름 예측")

    ppl_rows = table_after(people, "월별 인력 현황")
    dept_rows = table_after(people, "부서별 인원")
    shift_rows = table_after(people, "월별 근태·안전")
    wf_rows = table_after(people, "직군별 인건비 구성")

    cand_rows = table_after(recruit, "후보자 파이프라인")
    pos_rows = table_after(recruit, "채용 포지션")
    chan_rows = table_after(recruit, "채널별 채용 성과")

    proj_rows = table_after(projects_note, "주요 프로젝트·계약")
    decision_rows = table_after(summary, "의사결정 요청")

    # ── 핵심 지표(세로형) 합성: 재무·인력 표에서 파생 ──
    kpi = []

    def add_kpi(metric, cat, month, value):
        if value is None:
            return
        kpi.append({"지표": metric, "분류": cat, "값": value, "월": month,
                    "항목": "%s %s" % (metric, month)})

    for r in fin_rows:
        m = r["월"]
        add_kpi("매출", "재무", m, r.get("매출"))
        add_kpi("비용", "재무", m, r.get("비용"))
        add_kpi("영업이익", "재무", m, r.get("영업이익"))
        add_kpi("현금 잔고", "재무", m, r.get("현금 잔고"))
    for r in ppl_rows:
        m = r["월"]
        add_kpi("총원", "인력", m, r.get("총원"))
        add_kpi("입사", "인력", m, r.get("입사") or 0)
        add_kpi("퇴사", "인력", m, r.get("퇴사") or 0)
        add_kpi("인건비", "인력", m, r.get("인건비"))

    # ── 비용 구조: 가로형 → (월, 비용 유형, 금액) 세로형 ──
    cost_structure = []
    for r in cost_rows:
        for kind, key in (("고정비", "고정비"), ("변동비", "변동비")):
            cost_structure.append({"항목": "%s %s" % (kind, r["월"]), "월": r["월"],
                                   "비용 유형": kind, "금액": r.get(key)})

    # ── 채용: 포지션 의사 id 부여, 면접일 KST → UTC ──
    positions = []
    for p in pos_rows:
        p = dict(p)
        p["_id"] = pseudo_id(str(p["포지션명"]))
        positions.append(p)

    candidates = []
    for c in cand_rows:
        c = dict(c)
        pos_name = c.pop("지원 포지션", None)
        c["지원 포지션"] = [pseudo_id(str(pos_name))] if pos_name else []
        c["면접일"] = kst_to_utc_iso(c.get("면접일"))
        candidates.append(c)

    for r in mfg_rows:
        r.setdefault("항목", "시공원가 %s" % r["월"])
    for r in shift_rows:
        r.setdefault("항목", "근태·안전 %s" % r["월"])

    raw = {
        "fetchedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "obsidian",
        "databases": {
            "kpi": {"rows": kpi},
            "manufacturing": {"rows": mfg_rows},
            "costStructure": {"rows": cost_structure},
            "shiftSafety": {"rows": shift_rows},
            "departments": {"rows": dept_rows},
            "workforceCost": {"rows": wf_rows},
            "projects": {"rows": proj_rows},
            "candidates": {"rows": candidates},
            "positions": {"rows": positions},
            "channels": {"rows": chan_rows},
            "financeNotes": {"rows": fin_rows},
            "peopleNotes": {"rows": ppl_rows},
        },
    }

    # ── manual.json: 의사결정·현금흐름 예측·보고 제목 (볼트가 원본) ──
    props = frontmatter(summary)
    base = props.get("기준월", "")
    report = props.get("보고월", "")
    as_of, base_m = month_korean(base) if base else ("", 0)
    report_kr, _ = month_korean(report) if report else ("", 0)

    manual = {
        "_note": "이 파일은 fetch_obsidian.py가 옵시디언 볼트에서 생성합니다 — 직접 고치지 말고 볼트 노트를 수정하세요.",
        "asOf": as_of,
        "reportTitle": "%s 경영지원 보고 — %d월 실적 기준" % (report_kr, base_m),
        "decisions": [{"title": d["안건"], "desc": d["내용"], "due": str(d["기한"])}
                      for d in decision_rows],
        "cashForecast": [{"month": f["월"], "inflow": f["예상 유입"],
                          "outflow": f["예상 유출"], "balance": f["월말 예상 잔고"],
                          "note": f.get("비고") or ""} for f in forecast],
        "financeNotes": {r["월"]: r["비고"] for r in fin_rows if r.get("비고")},
        "peopleNotes": {r["월"]: r["비고"] for r in ppl_rows if r.get("비고")},
    }

    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(MANUAL_PATH, "w", encoding="utf-8") as f:
        json.dump(manual, f, ensure_ascii=False, indent=2)
        f.write("\n")

    months = sorted({r["월"] for r in mfg_rows})
    print("수집 완료(옵시디언): %d개월 %s~%s · 후보자 %d명 · 부서 %d개 · 안건 %d건"
          % (len(months), months[0], months[-1], len(candidates), len(dept_rows),
             len(decision_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
