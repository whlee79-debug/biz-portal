# -*- coding: utf-8 -*-
"""생성 — data/source.json → dashboard/assets/data.js

대시보드 4개 페이지가 읽는 전역 DATA 객체를 만듭니다. 파생 규칙(총비용·영업이익·
이익률·전사 인건비)은 tools/config.py의 DERIVED_FIELDS 주석에 정리돼 있습니다.

    python3 tools/build.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = os.path.join(ROOT, "data", "source.json")
OUT_PATH = os.path.join(ROOT, "dashboard", "assets", "data.js")

# 배열 뒤에 붙일 설명 주석 — 숫자만 봐서는 뜻이 안 잡히는 필드에만 답니다.
COMMENTS = {
    "output": "생산량(천 개)",
    "rawMaterial": "원료비(오일·보습제·기능성 원료)",
    "packaging": "부자재비(용기·캡·단상자·포장재)",
    "labor": "노무비(생산직 정직원)",
    "dispatch": "파견용역비(충전·포장 라인)",
    "overhead": "제조경비(전력·감가상각·수선·외부시험)",
    "total": "제조원가 합계",
    "sga": "판매관리비 (= 총비용 - 제조원가)",
    "unitCost": "개당 제조원가(원)",
    "defectPct": "공정 불량률(%)",
    "raw": "원료(글리세린·식물성 오일 등)",
    "container": "용기(PP·PET 수지)",
    "carton": "포장재(단상자·지류)",
    "laborCost": "정직원 인건비(생산직 노무비 + 사무직, 잔업·특근 포함 · 파견 별도)",
    "prodStaff": "생산직(정직원)",
    "officeStaff": "사무직(연구·영업·구매·경영지원)",
    "dispatchStaff": "파견직 평균 인원",
    "dispatchManDays": "파견 공수(연인원)",
    "overtimeHours": "잔업 시간(생산직 합계)",
    "holidayHours": "특근(휴일근로) 시간",
    "allowance": "잔업·특근 수당(백만 원)",
    "noAccidentDays": "무재해 일수(월말 누적)",
    "accidents": "산업재해 건수",
    "nearMiss": "아차사고 신고 건수",
}
COMMENT_COLUMN = 56  # 주석 시작 열 — 세로로 줄 맞춰 읽기 쉽게


def js(value):
    """JSON은 그대로 유효한 JS 리터럴입니다."""
    return json.dumps(value, ensure_ascii=False)


def js_obj(obj):
    """{ key: value } — 키가 식별자라 따옴표 없이 쓰는 편이 읽기 낫습니다."""
    return "{ %s }" % ", ".join("%s: %s" % (k, js(v)) for k, v in obj.items())


def rows(items, indent=4):
    """객체 배열을 한 줄에 하나씩 — 노션에서 한 행 고치면 한 줄만 바뀌도록."""
    if not items:
        return "[]"
    pad = " " * indent
    body = ",\n".join(pad + js_obj(item) for item in items)
    return "[\n%s\n%s]" % (body, " " * (indent - 2))


def block(fields):
    """`name: [...],  // 설명` 줄들을 묶어 하나의 블록 문자열로 만듭니다."""
    lines = []
    for i, (name, values) in enumerate(fields):
        trailing = "" if i == len(fields) - 1 else ","
        line = "    %s: %s%s" % (name, js(values), trailing)
        note = COMMENTS.get(name)
        if note:
            line += " " * max(1, COMMENT_COLUMN - len(line)) + "// " + note
        lines.append(line)
    return "\n".join(lines)


def main():
    with open(SOURCE_PATH, encoding="utf-8") as f:
        src = json.load(f)

    months = src["months"]
    kpi, mfg = src["kpi"], src["manufacturing"]
    n = len(months)

    # ── 파생 ────────────────────────────────────────────────────────
    cost = [mfg["total"][i] + mfg["sga"][i] for i in range(n)]
    profit = [kpi["revenue"][i] - cost[i] for i in range(n)]
    margin = [round(profit[i] * 100.0 / kpi["revenue"][i], 1) if kpi["revenue"][i] else 0
              for i in range(n)]

    office_cost = sum(d["cost"] for d in src["departments"] if d["group"] == "사무직")
    labor_cost = [mfg["labor"][i] + office_cost for i in range(n)]

    leaves_total = sum(v for v in kpi["leaves"] if v)
    avg_headcount = sum(kpi["headcount"]) / float(n)
    attrition = round(leaves_total * 100.0 / avg_headcount, 1) if avg_headcount else 0.0

    departments = [{"name": d["name"], "count": d["count"], "cost": d["cost"], "note": d["note"]}
                   for d in src["departments"]]

    content = """/* {title} (단위: {unit})
   ⚠️ 이 파일은 자동 생성됩니다 — 직접 고치지 마세요.
   옵시디언 BizPortal 볼트를 고친 뒤 `python3 tools/sync.py` 를 실행하세요.
   생성: {synced} · 원본: {fetch_source} · 모든 수치는 가상 데모 데이터 */
const DATA = {{
  asOf: {as_of},
  months: {months},
  monthLabels: {month_labels},

  finance: {{
{finance}
  }},

  costStructure: {{
{cost_structure}
  }},

  /* 제조원가 — 총비용 = 제조원가 + 판관비 로 정합 */
  manufacturing: {{
{manufacturing}
  }},

  /* 주요 원부자재 단가 지수 ({base_month} = 100) */
  materialIndex: {{
{material_index}
  }},

  cashForecast: {cash_forecast},

  people: {{
{people}
  }},

  /* 근태·파견 (경영지원 소관: 인건비·공수 관리) */
  shift: {{
{shift}
  }},

  /* 안전 (경영지원 취합·보고) */
  safety: {{
{safety}
  }},

  departments: {departments},

  decisions: {decisions},

  projects: {projects},

  recruiting: {{
    stages: {stages},
    candidates: {candidates},
    positions: {positions},
    channels: {channels}
  }}
}};
""".format(
        title=src["meta"].get("reportTitle") or "경영 현황 종합 대시보드",
        unit=src["meta"].get("unit", "백만 원"),
        synced=src["meta"].get("syncedAt", ""),
        fetch_source=src["meta"].get("fetchSource", ""),
        as_of=js(src["meta"].get("asOf", "")),
        months=js(months),
        month_labels=js(src["monthLabels"]),
        base_month=months[0],
        finance=block([
            ("revenue", kpi["revenue"]),
            ("cost", cost),
            ("profit", profit),
            ("cash", kpi["cash"]),
            ("marginPct", margin),
            ("notes", src["notes"]["finance"]),
        ]),
        cost_structure=block([
            ("fixed", src["costStructure"]["fixed"]),
            ("variable", src["costStructure"]["variable"]),
        ]),
        manufacturing=block([
            ("output", mfg["output"]),
            ("rawMaterial", mfg["rawMaterial"]),
            ("packaging", mfg["packaging"]),
            ("labor", mfg["labor"]),
            ("dispatch", mfg["dispatch"]),
            ("overhead", mfg["overhead"]),
            ("total", mfg["total"]),
            ("sga", mfg["sga"]),
            ("unitCost", mfg["unitCost"]),
            ("defectPct", mfg["defectPct"]),
            ("notes", mfg["notes"]),
        ]),
        material_index=block([
            ("raw", src["materialIndex"]["raw"]),
            ("container", src["materialIndex"]["container"]),
            ("carton", src["materialIndex"]["carton"]),
        ]),
        people=block([
            ("headcount", kpi["headcount"]),
            ("laborCost", labor_cost),
            ("joins", kpi["joins"]),
            ("leaves", kpi["leaves"]),
            ("notes", src["notes"]["people"]),
            ("attritionPct", attrition),
        ]),
        shift=block([
            ("prodStaff", src["shift"]["prodStaff"]),
            ("officeStaff", src["shift"]["officeStaff"]),
            ("dispatchStaff", src["shift"]["dispatchStaff"]),
            ("dispatchManDays", src["shift"]["dispatchManDays"]),
            ("overtimeHours", src["shift"]["overtimeHours"]),
            ("holidayHours", src["shift"]["holidayHours"]),
            ("allowance", src["shift"]["allowance"]),
        ]),
        safety=block([
            ("noAccidentDays", src["safety"]["noAccidentDays"]),
            ("accidents", src["safety"]["accidents"]),
            ("nearMiss", src["safety"]["nearMiss"]),
        ]),
        cash_forecast=rows(src["cashForecast"]),
        departments=rows(departments),
        decisions=rows(src["decisions"]),
        projects=rows(src["projects"]),
        stages=js(src["recruiting"]["stages"]),
        candidates=rows(src["recruiting"]["candidates"], indent=6),
        positions=rows(src["recruiting"]["positions"], indent=6),
        channels=rows(src["recruiting"]["channels"], indent=6),
    )

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("생성 완료: dashboard/assets/data.js (%s 기준, %d개월)"
          % (src["meta"].get("asOf", "?"), n))
    print("  총비용 %s / 영업이익 %s / 이익률 %s%% / 전사 인건비 %s (파생값, %s)"
          % (cost[-1], profit[-1], margin[-1], labor_cost[-1], months[-1]))


if __name__ == "__main__":
    main()
