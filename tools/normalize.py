# -*- coding: utf-8 -*-
"""정규화 — data/notion-raw.json + data/manual.json → data/source.json

노션 원본은 DB마다 행 구조가 제각각이라(세로형 지표 DB, 월별 가로형 DB, 관계형
채용 DB) 그대로는 다루기 어렵습니다. 여기서 월 배열 기준의 평평한 구조로 바꿉니다.
파생·검증은 하지 않습니다 — 그건 verify.py / build.py 몫입니다.

    python3 tools/normalize.py
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DEPT_GROUP, KST_OFFSET_HOURS, RECRUIT_STAGES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "data", "notion-raw.json")
MANUAL_PATH = os.path.join(ROOT, "data", "manual.json")
OUT_PATH = os.path.join(ROOT, "data", "source.json")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def page_id(value):
    """관계형 속성 값(페이지 id 또는 URL)에서 32자리 id만 뽑아냅니다."""
    if not value:
        return ""
    text = value if isinstance(value, str) else str(value)
    hexes = re.findall(r"[0-9a-fA-F]{32}", text.replace("-", ""))
    return hexes[-1].lower() if hexes else ""


def to_kst(iso_utc):
    """노션은 면접일을 UTC로 저장합니다. 대시보드 표기는 KST 기준입니다."""
    if not iso_utc:
        return ""
    text = iso_utc.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return ""
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None) - dt.utcoffset()
    return (dt + timedelta(hours=KST_OFFSET_HOURS)).strftime("%Y-%m-%d %H:%M")


def rows(raw, key):
    return raw["databases"].get(key, {}).get("rows", [])


def series(by_month, months, field, default=None):
    return [by_month.get(m, {}).get(field, default) for m in months]


def main():
    raw = load(RAW_PATH)
    manual = load(MANUAL_PATH)

    # ── 월 축: 시공원가 표를 기준으로 잡습니다(가장 촘촘하고 최신) ──
    mfg_by_month = {r["월"]: r for r in rows(raw, "manufacturing")}
    months = sorted(mfg_by_month)
    if not months:
        sys.exit("오류: 월별 시공원가 표가 비어 있어 월 축을 만들 수 없습니다.")
    month_labels = ["%d월" % int(m.split("-")[1]) for m in months]

    # ── 경영 핵심 지표: 세로형(지표·월·값) → 지표별 월 배열 ──
    kpi_raw = {}
    for r in rows(raw, "kpi"):
        kpi_raw.setdefault(r["지표"], {})[r["월"]] = r["값"]

    def kpi(name):
        return [kpi_raw.get(name, {}).get(m) for m in months]

    # ── 비용 구조: (월, 비용 유형) → 금액 ──
    # manual.json에 override가 있으면 그쪽이 이깁니다(노션 DB가 아직 옛 기준일 때의 임시 조치).
    cost_struct = {}
    for r in rows(raw, "costStructure"):
        cost_struct.setdefault(r["비용 유형"], {})[r["월"]] = r["금액"]

    override = manual.get("costStructureOverride") or {}
    for month, values in override.items():
        cost_struct.setdefault("고정비", {})[month] = values["fixed"]
        cost_struct.setdefault("변동비", {})[month] = values["variable"]

    shift_by_month = {r["월"]: r for r in rows(raw, "shiftSafety")}

    # ── 채용: 포지션 관계 해석 ──
    positions = rows(raw, "positions")
    pos_name = {page_id(p.get("_id", "")): p["포지션명"] for p in positions}

    candidates = []
    for c in rows(raw, "candidates"):
        rel = c.get("지원 포지션") or []
        linked = [pos_name.get(page_id(x), "") for x in rel]
        candidates.append({
            "name": c["이름"],
            "position": next((n for n in linked if n), ""),
            "stage": c["상태"],
            "applied": c.get("지원일") or "",
            "channel": c.get("지원 경로") or "",
            "rating": c.get("평가") or "",
            "interview": to_kst(c.get("면접일")),
            "memo": c.get("메모") or "",
        })
    # 칸반 단계 순 → 같은 단계면 지원일 순
    candidates.sort(key=lambda c: (
        RECRUIT_STAGES.index(c["stage"]) if c["stage"] in RECRUIT_STAGES else 99,
        c["applied"],
    ))

    # ── 비고: 노션 DB에서 수집됐으면 그걸 쓰고, 아니면 manual.json 폴백 ──
    def notes_from(db_key, manual_key):
        collected = {r["월"]: (r.get("비고") or "") for r in rows(raw, db_key)}
        return collected if collected else manual.get(manual_key, {})

    finance_notes = notes_from("financeNotes", "financeNotes")
    people_notes = notes_from("peopleNotes", "peopleNotes")

    source = {
        "meta": {
            "asOf": manual.get("asOf", ""),
            "reportTitle": manual.get("reportTitle", ""),
            "syncedAt": raw.get("fetchedAt", ""),
            "fetchSource": raw.get("source", ""),
            "unit": "백만 원",
            "costStructureOverride": sorted(override),
        },
        "months": months,
        "monthLabels": month_labels,

        "kpi": {
            "revenue": kpi("매출"),
            "cash": kpi("현금 잔고"),
            "headcount": kpi("총원"),
            "joins": kpi("입사"),
            "leaves": kpi("퇴사"),
            # 아래 3개는 파생값으로 대체되지만, 노션과의 어긋남을 잡기 위해 남겨둡니다.
            "reported": {
                "cost": kpi("비용"),
                "profit": kpi("영업이익"),
                "laborCost": kpi("인건비"),
            },
        },

        "manufacturing": {
            "material": series(mfg_by_month, months, "재료비"),
            "labor": series(mfg_by_month, months, "노무비"),
            "dayLabor": series(mfg_by_month, months, "일용노무비"),
            "equipment": series(mfg_by_month, months, "장비비"),
            "outsourcing": series(mfg_by_month, months, "외주비"),
            "total": series(mfg_by_month, months, "시공원가"),
            "sga": series(mfg_by_month, months, "판관비"),
            "output": series(mfg_by_month, months, "시공량(m)"),
            "unitCost": series(mfg_by_month, months, "m당 시공원가(만원)"),
            "notes": [mfg_by_month.get(m, {}).get("비고") or "" for m in months],
        },

        "materialIndex": {
            "cement": series(mfg_by_month, months, "시멘트 지수"),
            "chem": series(mfg_by_month, months, "약액 지수"),
            "fuel": series(mfg_by_month, months, "유류 지수"),
        },

        "costStructure": {
            "fixed": [cost_struct.get("고정비", {}).get(m) for m in months],
            "variable": [cost_struct.get("변동비", {}).get(m) for m in months],
        },

        "shift": {
            "fieldStaff": series(shift_by_month, months, "현장직"),
            "officeStaff": series(shift_by_month, months, "내근직"),
            "dayWorkers": series(shift_by_month, months, "일용직"),
            "dayManDays": series(shift_by_month, months, "일용 공수"),
            "overtimeHours": series(shift_by_month, months, "잔업시간"),
            "holidayHours": series(shift_by_month, months, "특근시간"),
            "allowance": series(shift_by_month, months, "잔업·특근 수당"),
        },
        "safety": {
            "noAccidentDays": series(shift_by_month, months, "무재해 일수"),
            "accidents": series(shift_by_month, months, "산업재해 건수"),
            "nearMiss": series(shift_by_month, months, "아차사고 건수"),
        },

        "departments": [
            {
                "name": d["부서"],
                "count": d["인원"],
                "cost": d["월 인건비"],
                "note": d.get("비고") or "",
                "group": DEPT_GROUP.get(d["부서"], "미분류"),
            }
            for d in rows(raw, "departments")
        ],

        "workforceCost": [
            {
                "group": w["직군"],
                "kind": w.get("구분", ""),
                "count": w["인원"],
                "avgSalary": w.get("평균 연봉(만원)"),
                "salaryTotal": w.get("연봉 총액(백만원)"),
                "statutory": w.get("법정부담·충당(백만원)"),
                "annualTotal": w.get("연간 총부담(백만원)"),
                "includes": w.get("포함 부서", ""),
            }
            for w in rows(raw, "workforceCost")
        ],

        "projects": [
            {
                "name": p["항목"],
                "type": p.get("구분", ""),
                "dept": p.get("담당 부서", ""),
                "status": p.get("상태", ""),
                "progress": p.get("진행률(%)", 0),
                "due": p.get("마감일", ""),
                "note": p.get("리스크/비고") or "",
            }
            for p in rows(raw, "projects")
        ],

        "recruiting": {
            "stages": RECRUIT_STAGES,
            "candidates": candidates,
            "positions": [
                {
                    "name": p["포지션명"],
                    "dept": p.get("부서", ""),
                    "type": p.get("고용형태", ""),
                    "count": p.get("채용 인원", 0),
                    "opened": p.get("오픈일", ""),
                    "target": p.get("마감 목표일", ""),
                    "status": p.get("진행 상태", ""),
                }
                for p in positions
            ],
            "channels": [
                {
                    "name": c["채널"],
                    "applied": c.get("지원", 0),
                    "screened": c.get("서류합격", 0),
                    "interviewed": c.get("면접합격", 0),
                    "offered": c.get("오퍼", 0),
                    "hired": c.get("입사", 0),
                    "spend": c.get("집행 비용(만원)", 0),
                    "costPerHire": c.get("1명당 원가(만원)", 0),
                    "daysToHire": c.get("소요일", 0),
                    "note": c.get("비고", ""),
                }
                for c in rows(raw, "channels")
            ],
        },

        "cashForecast": manual.get("cashForecast", []),
        "decisions": manual.get("decisions", []),
        "notes": {
            "finance": [finance_notes.get(m, "") for m in months],
            "people": [people_notes.get(m, "") for m in months],
        },
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(source, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("정규화 완료: data/source.json (%d개월 %s~%s, 후보자 %d명, 부서 %d개)"
          % (len(months), months[0], months[-1], len(candidates), len(source["departments"])))


if __name__ == "__main__":
    main()
