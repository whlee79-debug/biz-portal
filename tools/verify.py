# -*- coding: utf-8 -*-
"""검증 — data/source.json의 정합성을 확인합니다.

대시보드에 틀린 숫자가 올라가는 걸 막는 게 목적입니다. 두 종류를 봅니다.

  [오류] 자체 모순. 배포를 막습니다. (예: 재료비+노무비+제조경비 ≠ 제조원가)
  [경고] 노션 DB끼리 어긋남. 어느 쪽이 맞는지는 사람이 판단해야 하므로,
         어떤 DB의 어떤 값을 고쳐야 하는지 짚어주고 배포는 진행합니다.

    python3 tools/verify.py            # 오류만 배포 차단
    python3 tools/verify.py --strict   # 경고도 배포 차단
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import TOLERANCE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = os.path.join(ROOT, "data", "source.json")

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def check_series(src):
    """모든 월 배열이 같은 길이이고 빈 칸이 없는지."""
    n = len(src["months"])
    groups = ["manufacturing", "materialIndex", "costStructure", "shift", "safety"]
    for group in groups:
        for field, values in src[group].items():
            if field == "notes":
                continue
            if len(values) != n:
                err("%s.%s 길이가 %d (월 %d개와 불일치)" % (group, field, len(values), n))
            for i, v in enumerate(values):
                if v is None:
                    err("%s.%s 의 %s 값이 비어 있습니다 — 노션에 해당 월 행이 없습니다."
                        % (group, field, src["months"][i]))
    for field in ("revenue", "cash", "headcount", "joins", "leaves"):
        values = src["kpi"][field]
        for i, v in enumerate(values):
            if v is None:
                err("경영 핵심 지표 DB에 '%s' %s 행이 없습니다." % (field, src["months"][i]))


def check_manufacturing(src):
    """시공원가 내부 정합 — 이건 자체 모순이므로 오류."""
    m, months = src["manufacturing"], src["months"]
    for i, month in enumerate(months):
        parts = (m["material"][i], m["labor"][i], m["dayLabor"][i],
                 m["equipment"][i], m["outsourcing"][i])
        if None in parts:
            continue
        total = sum(parts)
        if not close(total, m["total"][i], TOLERANCE["money"]):
            err("%s 시공원가 %s ≠ 재료비+노무비+일용노무비+장비비+외주비 %s (재무 노트 시공원가 표)"
                % (month, m["total"][i], total))
        if m["output"][i]:
            unit = m["total"][i] * 100.0 / m["output"][i]
            if not close(unit, m["unitCost"][i], TOLERANCE["unitCost"]):
                err("%s m당 시공원가 %s만 원 ≠ 시공원가÷시공량 %.2f만 원 (재무 노트 시공원가 표)"
                    % (month, m["unitCost"][i], unit))


def check_derived_vs_notion(src):
    """파생값과 노션이 들고 있는 값의 어긋남 — 어느 쪽이 맞는지는 사람 판단."""
    months, kpi, m = src["months"], src["kpi"], src["manufacturing"]
    office = sum(d["cost"] for d in src["departments"] if d["group"] == "내근직")

    drift_cost, drift_profit, drift_labor = [], [], []
    for i, month in enumerate(months):
        cost = m["total"][i] + m["sga"][i]
        profit = kpi["revenue"][i] - cost
        labor = m["labor"][i] + office

        reported_cost = kpi["reported"]["cost"][i]
        reported_profit = kpi["reported"]["profit"][i]
        reported_labor = kpi["reported"]["laborCost"][i]

        if reported_cost is not None and not close(cost, reported_cost, TOLERANCE["money"]):
            drift_cost.append("%s %s→%s" % (month, reported_cost, cost))
        if reported_profit is not None and not close(profit, reported_profit, TOLERANCE["money"]):
            drift_profit.append("%s %s→%s" % (month, reported_profit, profit))
        if reported_labor is not None and not close(labor, reported_labor, TOLERANCE["money"]):
            drift_labor.append("%s %s→%s" % (month, reported_labor, labor))

    if drift_cost:
        warn("📈 경영 핵심 지표 DB '비용'이 제조원가+판관비와 다릅니다 — %s\n"
             "        → 대시보드는 제조원가 DB 기준으로 그립니다. 노션 '비용' 행을 갱신하세요."
             % ", ".join(drift_cost))
    if drift_profit:
        warn("📈 경영 핵심 지표 DB '영업이익'이 매출−비용과 다릅니다 — %s" % ", ".join(drift_profit))
    if drift_labor:
        warn("인력 현황 표 '인건비'가 노무비(직영)+내근직 인건비(%d)와 다릅니다 — %s"
             % (office, ", ".join(drift_labor)))


def check_cost_structure(src):
    """고정비+변동비 = 총비용.

    파생 규칙이 없어 노션 값을 그대로 쓰는 자리라, 어긋나면 대시보드에 틀린 그래프가
    바로 올라갑니다. 그래서 오류로 막습니다. manual.json override가 걸려 있으면
    이미 사람이 손으로 맞춰 둔 것이므로, 노션을 갱신하라는 경고만 남깁니다.
    """
    months, m, cs = src["months"], src["manufacturing"], src["costStructure"]
    overridden = set(src["meta"].get("costStructureOverride") or [])
    gaps = []
    for i, month in enumerate(months):
        if cs["fixed"][i] is None or cs["variable"][i] is None:
            continue
        total = m["total"][i] + m["sga"][i]
        s = cs["fixed"][i] + cs["variable"][i]
        if not close(s, total, TOLERANCE["money"]):
            gaps.append("%s %s≠%s" % (month, s, total))
    if gaps:
        err("🧾 월별 비용 구조 DB의 고정비+변동비가 총비용과 다릅니다 — %s\n"
            "        → 노션에서 고정비/변동비를 다시 나누거나, data/manual.json의 "
            "costStructureOverride로 임시 지정하세요." % ", ".join(gaps))
    if overridden:
        warn("고정비/변동비 %d개월치를 data/manual.json override로 쓰고 있습니다(%s~%s).\n"
             "        → 🧾 월별 비용 구조 DB를 갱신한 뒤 override 블록을 지우면 노션이 원본이 됩니다."
             % (len(overridden), min(overridden), max(overridden)))


def check_people(src):
    """인원·인건비 교차 검증."""
    months, kpi, shift, m = src["months"], src["kpi"], src["shift"], src["manufacturing"]
    for i, month in enumerate(months):
        staff = shift["fieldStaff"][i] + shift["officeStaff"][i]
        if staff != kpi["headcount"][i]:
            err("%s 현장직+내근직 %d명 ≠ 총원 %d명 (근태·안전 표 vs 인력 현황 표)"
                % (month, staff, kpi["headcount"][i]))

    latest = len(months) - 1
    dept_count = sum(d["count"] for d in src["departments"])
    if dept_count != kpi["headcount"][latest]:
        err("부서별 인원 합계 %d명 ≠ %s 총원 %d명 (부서별 인원 표)"
            % (dept_count, months[latest], kpi["headcount"][latest]))

    field_cost = sum(d["cost"] for d in src["departments"] if d["group"] == "현장직")
    if not close(field_cost, m["labor"][latest], TOLERANCE["money"]):
        err("현장직 부서 인건비 합계 %s ≠ %s 노무비(직영) %s (부서별 인원 표 vs 시공원가 표)"
            % (field_cost, months[latest], m["labor"][latest]))

    unassigned = [d["name"] for d in src["departments"] if d["group"] == "미분류"]
    if unassigned:
        err("직군이 지정되지 않은 부서: %s — tools/config.py의 DEPT_GROUP에 추가하세요."
            % ", ".join(unassigned))

    wf_count = sum(w["count"] for w in src["workforceCost"])
    if wf_count and wf_count != kpi["headcount"][latest]:
        warn("🧮 직군별 인건비 구성 인원 합계 %d명 ≠ 총원 %d명"
             % (wf_count, kpi["headcount"][latest]))


def check_recruiting(src):
    rec = src["recruiting"]
    stages = set(rec["stages"])
    for c in rec["candidates"]:
        if c["stage"] not in stages:
            err("후보자 '%s'의 단계 '%s'가 정의된 칸반 단계에 없습니다 — "
                "tools/config.py의 RECRUIT_STAGES를 확인하세요." % (c["name"], c["stage"]))
        if not c["position"]:
            err("후보자 '%s'에 지원 포지션이 연결되어 있지 않습니다 (노션 관계형 속성)." % c["name"])

    hired = sum(ch["hired"] for ch in rec["channels"])
    joins = sum(v for v in src["kpi"]["joins"] if v)
    if rec["channels"] and hired != joins:
        warn("📊 채널별 입사 합계 %d명 ≠ 📈 핵심 지표 입사 누계 %d명" % (hired, joins))


def check_cash_forecast(src):
    """예측 첫 달 잔고가 마지막 실적 잔고에서 이어지는지."""
    fc = src.get("cashForecast") or []
    if not fc:
        return
    last_cash = src["kpi"]["cash"][-1]
    expected = last_cash + fc[0]["inflow"] - fc[0]["outflow"]
    if not close(expected, fc[0]["balance"], TOLERANCE["money"]):
        warn("현금흐름 예측 %s 잔고 %s ≠ 직전 잔고 %s + 유입 − 유출 = %s (data/manual.json)"
             % (fc[0]["month"], fc[0]["balance"], last_cash, expected))


def check_wording(src):
    """같은 대상을 두 가지로 적어 둔 경우(오타 등)를 잡습니다."""
    blob = json.dumps(src, ensure_ascii=False)
    if "그라우딩" in blob:
        warn("표기 흔들림: '그라우딩'은 '그라우팅'의 오기일 가능성이 큽니다 — 볼트에서 통일하세요.")


def main():
    strict = "--strict" in sys.argv
    with open(SOURCE_PATH, encoding="utf-8") as f:
        src = json.load(f)

    check_series(src)
    check_manufacturing(src)
    check_derived_vs_notion(src)
    check_cost_structure(src)
    check_people(src)
    check_recruiting(src)
    check_cash_forecast(src)
    check_wording(src)

    for w in warnings:
        print("[경고] %s" % w)
    for e in errors:
        print("[오류] %s" % e)

    if errors:
        print("\n검증 실패: 오류 %d건 — 배포를 중단합니다." % len(errors))
        return 1
    if warnings and strict:
        print("\n검증 실패(--strict): 경고 %d건 — 배포를 중단합니다." % len(warnings))
        return 1
    print("\n검증 통과 (오류 0건, 경고 %d건)" % len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
