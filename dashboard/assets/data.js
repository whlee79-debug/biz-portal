/* 2026년 8월 경영지원 보고 — 7월 실적 기준 (단위: 백만 원)
   ⚠️ 이 파일은 자동 생성됩니다 — 직접 고치지 마세요.
   노션 '경영 현황 종합 대시보드'를 고친 뒤 `python3 tools/sync.py` 를 실행하세요.
   생성: 2026-08-04T15:49:33+09:00 · 원본: 노션(notion-api) · 모든 수치는 가상 데모 데이터 */
const DATA = {
  asOf: "2026년 7월",
  months: ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"],
  monthLabels: ["1월", "2월", "3월", "4월", "5월", "6월", "7월"],

  finance: {
    revenue: [420, 450, 480, 460, 510, 530, 545],
    cost: [390, 397, 419, 416, 432, 439, 448],
    profit: [30, 53, 61, 44, 78, 91, 97],
    cash: [850, 910, 960, 1010, 1080, 1170, 1255],
    marginPct: [7.1, 11.8, 12.7, 9.6, 15.3, 17.2, 17.8],
    notes: ["연초 계약 갱신 집중", "", "신규 거래처 2곳 추가", "ERP 1차 비용 집행", "분기 최고 실적", "A사 연간 계약 체결, 상반기 최고 실적", "A사 계약 매출 첫 반영, 월간 최고 실적"]
  },

  costStructure: {
    fixed: [200, 201, 210, 212, 214, 215, 217],
    variable: [190, 196, 209, 204, 218, 224, 231]
  },

  /* 제조원가 — 총비용 = 제조원가 + 판관비 로 정합 */
  manufacturing: {
    output: [1180, 1260, 1340, 1300, 1440, 1500, 1540], // 생산량(대)
    material: [175, 180, 192, 188, 200, 205, 210],      // 재료비
    labor: [98, 97, 103, 105, 110, 114, 116],           // 노무비(생산직)
    overhead: [40, 42, 44, 44, 45, 45, 46],             // 제조경비(감가상각·전력·수선)
    total: [313, 319, 339, 337, 355, 364, 372],         // 제조원가 합계
    sga: [77, 78, 80, 79, 77, 75, 76],                  // 판매관리비 (= 총비용 - 제조원가)
    unitCost: [26.5, 25.3, 25.3, 25.9, 24.7, 24.3, 24.2], // 대당 제조원가(만 원)
    notes: ["", "", "신규 라인 시운전", "폼 단가 인상 반영", "가동률 개선", "규모 효과로 대당 원가 최저", "A사 물량 반영, 대당 원가 최저 경신"]
  },

  /* 주요 원자재 단가 지수 (2026-01 = 100) */
  materialIndex: {
    foam: [100, 101.6, 104.7, 107.8, 110, 108.8, 109.4], // 우레탄폼
    spring: [100, 100, 103.9, 105.3, 106.6, 105.3, 106.6], // 포켓스프링(강선)
    fabric: [100, 101.3, 102.6, 103.9, 107.9, 109.2, 110.5] // 원단
  },

  cashForecast: [
    { month: "2026-08", inflow: 520, outflow: 480, balance: 1295, note: "ERP 잔여 예산 집행 반영" },
    { month: "2026-09", inflow: 555, outflow: 470, balance: 1380, note: "공장 임대 재계약 결과 반영" },
    { month: "2026-10", inflow: 560, outflow: 485, balance: 1455, note: "하반기 생산직 충원 인건비 반영" }
  ],

  people: {
    headcount: [42, 42, 43, 44, 45, 46, 46],
    laborCost: [145, 144, 150, 152, 157, 161, 163],     // 전사 인건비(생산직 노무비 + 사무직, 잔업·특근 포함)
    joins: [1, 0, 2, 1, 1, 1, 0],
    leaves: [0, 0, 1, 0, 0, 0, 0],
    notes: ["", "", "영업 1명 퇴사", "", "인사 인턴 정규 전환", "봉제·조립 생산직 1명 입사", "하반기 충원 3명 전형 진행 중"],
    attritionPct: 2.3
  },

  /* 교대·근태 (경영지원 소관: 인건비 변동 관리) */
  shift: {
    fieldStaff: [30, 30, 31, 32, 33, 34, 34],           // 생산직(현장)
    officeStaff: [12, 12, 12, 12, 12, 12, 12],          // 사무직
    overtimeHours: [980, 950, 1180, 1120, 1290, 1340, 1420], // 잔업 시간(생산직 합계)
    holidayHours: [180, 160, 240, 210, 290, 320, 340],  // 특근(휴일근로) 시간
    allowance: [9, 8, 11, 10, 12, 13, 15]               // 잔업·특근 수당(백만 원)
  },

  /* 안전 (경영지원 취합·보고) */
  safety: {
    noAccidentDays: [92, 120, 151, 181, 212, 242, 273], // 무재해 일수(월말 누적)
    accidents: [0, 0, 0, 0, 0, 0, 0],                   // 산업재해 건수
    nearMiss: [2, 1, 3, 2, 1, 2, 1]                     // 아차사고 신고 건수
  },

  departments: [
    { name: "물류·출하", count: 5, cost: 17, note: "압축포장·출하" },
    { name: "경영지원", count: 4, cost: 15, note: "인사·회계·총무 / 인턴 정규 전환 완료" },
    { name: "품질관리", count: 5, cost: 17, note: "입고·공정·출하 검사 / 품질관리 1명 채용 중" },
    { name: "생산", count: 24, cost: 82, note: "스프링·폼재단·퀼팅·봉제·조립 5개 공정" },
    { name: "영업", count: 4, cost: 17, note: "B2B(호텔·가구점)·B2C" },
    { name: "자재·구매", count: 4, cost: 15, note: "원자재 수급·재고 관리" }
  ],

  decisions: [
    { title: "ERP 가동 일정·교육 계획 승인", desc: "9월 말 가동 목표, 공정별 교육 일정 확정", due: "9/12" },
    { title: "공장 임대 재계약 최종 결정", desc: "임대료 인상률 5% 협상안 수용 여부", due: "9/26" },
    { title: "하반기 생산직 충원 계획 승인", desc: "봉제·조립 2명 추가, 설비보전 1명 신설", due: "10/16" }
  ],

  projects: [
    { name: "ISO 9001 인증 갱신", type: "인증/규제", dept: "품질관리", status: "3. 완료", progress: 100, due: "2026-05-30", note: "5/28 갱신 완료" },
    { name: "ERP 시스템 도입", type: "프로젝트", dept: "경영지원", status: "2. 진행중", progress: 88, due: "2026-09-30", note: "2차 예산 승인 완료(6/19) — 9월 말 가동 목표" },
    { name: "A사 호텔체인 연간 공급 계약", type: "계약", dept: "영업", status: "3. 완료", progress: 100, due: "2026-06-30", note: "6/25 계약 체결 — 7월부터 매출 반영 (연 +60 전망)" },
    { name: "노후 퀼팅기 교체 검토", type: "프로젝트", dept: "생산", status: "4. 보류", progress: 10, due: "2026-12-15", note: "투자 규모 검토 중, 4분기 재논의" },
    { name: "공장 임대 재계약", type: "계약", dept: "경영지원", status: "2. 진행중", progress: 60, due: "2026-09-26", note: "인상률 5%로 재협상 중 — 9월 하순 결론 예정" }
  ],

  recruiting: {
    stages: ["1. 신규 지원자 수신", "2. 서류 합격(면접 대기)", "3. 면접 진행", "4. 오퍼 제안", "5. 최종 합격", "6. 불합격"],
    candidates: [
      { name: "오세훈", position: "봉제·조립 생산직", stage: "1. 신규 지원자 수신", applied: "2026-07-16", channel: "채용사이트", rating: "", interview: "", memo: "가구 봉제 6년, 산업용 재봉기 숙련" },
      { name: "이서연", position: "품질관리 담당", stage: "2. 서류 합격(면접 대기)", applied: "2026-06-10", channel: "직접 지원", rating: "", interview: "2026-08-21 10:30", memo: "침구 QC 4년, ISO 9001 내부심사원 — 8/21 면접 예정" },
      { name: "김민준", position: "봉제·조립 생산직", stage: "3. 면접 진행", applied: "2026-06-08", channel: "채용사이트", rating: "", interview: "2026-08-13 14:00", memo: "매트리스 조립 5년 — 8/13 실기 평가 예정" },
      { name: "최수아", position: "설비보전 기사", stage: "4. 오퍼 제안", applied: "2026-06-03", channel: "추천", rating: "A (적극 추천)", interview: "2026-06-18 19:30", memo: "퀼팅기·재봉기 보전 경험 — 9/1 입사 목표" },
      { name: "정다은", position: "경영지원 인턴", stage: "5. 최종 합격", applied: "2026-03-15", channel: "채용사이트", rating: "A (적극 추천)", interview: "", memo: "5/1 입사 완료" },
      { name: "박지훈", position: "봉제·조립 생산직", stage: "5. 최종 합격", applied: "2026-05-28", channel: "헤드헌터", rating: "B (추천)", interview: "2026-06-16 23:00", memo: "6/22 입사 완료 (봉제·조립)" },
      { name: "한도현", position: "봉제·조립 생산직", stage: "6. 불합격", applied: "2026-05-20", channel: "채용사이트", rating: "D (비추천)", interview: "", memo: "경력 요건 미달" }
    ],
    positions: [
      { name: "설비보전 기사", dept: "생산", type: "계약직", count: 1, opened: "2026-06-01", target: "2026-09-30", status: "진행중" },
      { name: "경영지원 인턴", dept: "경영지원", type: "인턴", count: 1, opened: "2026-03-01", target: "2026-04-30", status: "마감" },
      { name: "품질관리 담당", dept: "품질관리", type: "정규직", count: 1, opened: "2026-05-15", target: "2026-09-30", status: "진행중" },
      { name: "봉제·조립 생산직", dept: "생산", type: "정규직", count: 2, opened: "2026-05-01", target: "2026-10-31", status: "진행중" }
    ],
    channels: [
      { name: "채용사이트", applied: 68, screened: 22, interviewed: 9, offered: 3, hired: 3, spend: 180, costPerHire: 60, daysToHire: 42, note: "유입은 가장 많고 원가도 최저 — 생산직 채용 주력 채널" },
      { name: "헤드헌터", applied: 6, screened: 5, interviewed: 3, offered: 2, hired: 1, spend: 850, costPerHire: 850, daysToHire: 35, note: "원가 최고 — 설비보전 등 확보 어려운 직군에만 선별 사용" },
      { name: "직접 지원", applied: 21, screened: 7, interviewed: 3, offered: 1, hired: 0, spend: 0, costPerHire: 0, daysToHire: 38, note: "비용 0이나 상반기 입사 0명(품질관리 1명 면접 진행 중)" },
      { name: "추천", applied: 12, screened: 9, interviewed: 6, offered: 2, hired: 2, spend: 200, costPerHire: 100, daysToHire: 24, note: "소요일 최단(24일)·서류 통과율 높음 — 사내 추천 포상금" }
    ]
  }
};
