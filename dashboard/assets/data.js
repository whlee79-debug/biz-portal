/* 2026년 7월 보고 — 6월 실적 기준 (노션 '경영 현황 종합 대시보드' 동기화, 단위: 백만 원) */
const DATA = {
  asOf: "2026년 6월",
  months: ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
  monthLabels: ["1월", "2월", "3월", "4월", "5월", "6월"],

  finance: {
    revenue: [420, 450, 480, 460, 510, 530],
    cost: [360, 370, 390, 385, 400, 405],
    profit: [60, 80, 90, 75, 110, 125],
    cash: [850, 910, 960, 1010, 1080, 1170],
    marginPct: [14.3, 17.8, 18.8, 16.3, 21.6, 23.6],
    notes: ["연초 계약 갱신 집중", "", "신규 거래처 2곳 추가", "ERP 1차 비용 집행", "분기 최고 실적", "A사 연간 계약 체결, 상반기 최고 실적"]
  },

  costStructure: {
    fixed: [245, 245, 252, 258, 264, 267],
    variable: [115, 125, 138, 127, 136, 138]
  },

  cashForecast: [
    { month: "2026-07", inflow: 540, outflow: 455, balance: 1255, note: "A사 연간 계약 첫 월 정산 반영" },
    { month: "2026-08", inflow: 520, outflow: 475, balance: 1300, note: "ERP 잔여 예산·임대 재계약 결과 반영" },
    { month: "2026-09", inflow: 555, outflow: 465, balance: 1390, note: "하반기 채용 인건비 반영" }
  ],

  people: {
    headcount: [42, 42, 43, 44, 45, 46],
    laborCost: [210, 210, 216, 222, 228, 234],
    joins: [1, 0, 2, 1, 1, 1],
    leaves: [0, 0, 1, 0, 0, 0],
    notes: ["", "", "영업 1명 퇴사", "", "인사 인턴 정규 전환", "백엔드 개발자 1명 입사"],
    attritionPct: 2.3
  },

  departments: [
    { name: "개발", count: 19, cost: 108, note: "백엔드 1명 입사 완료, 1명 추가 채용 중" },
    { name: "영업", count: 9, cost: 45, note: "" },
    { name: "경영지원", count: 7, cost: 28, note: "인사 인턴 정규 전환 완료" },
    { name: "마케팅", count: 6, cost: 27, note: "콘텐츠 마케터 1명 채용 중" },
    { name: "디자인", count: 5, cost: 26, note: "프로덕트 디자이너 1명 채용 중" }
  ],

  decisions: [
    { title: "ERP 가동 일정·교육 계획 승인", desc: "8월 말 가동 목표, 부서별 교육 일정 확정", due: "7/31" },
    { title: "사무실 임대 재계약 최종 결정", desc: "인상률 5% 협상안 수용 여부", due: "8/8" },
    { title: "하반기 채용 계획 승인", desc: "백엔드 1명 추가·데이터 분석가 신설", due: "8/14" }
  ],

  projects: [
    { name: "ISO 9001 인증 갱신", type: "인증/규제", dept: "경영지원", status: "3. 완료", progress: 100, due: "2026-05-30", note: "5/28 갱신 완료" },
    { name: "ERP 시스템 도입", type: "프로젝트", dept: "경영지원", status: "2. 진행중", progress: 85, due: "2026-08-31", note: "2차 예산 승인 완료(6/19) — 8월 말 가동 목표" },
    { name: "A사 연간 공급 계약", type: "계약", dept: "영업", status: "3. 완료", progress: 100, due: "2026-06-30", note: "6/25 계약 체결 완료 — 연 매출 +60 전망" },
    { name: "사무실 임대 재계약", type: "계약", dept: "경영지원", status: "2. 진행중", progress: 60, due: "2026-08-08", note: "인상률 5%로 재협상 중 — 8월 초 결론 예정" },
    { name: "법인차량 리스 갱신", type: "계약", dept: "경영지원", status: "4. 보류", progress: 10, due: "2026-09-30", note: "우선순위 낮음, 3분기 재검토" }
  ],

  recruiting: {
    stages: ["1. 신규 지원자 수신", "2. 서류 합격(면접 대기)", "3. 면접 진행", "4. 오퍼 제안", "5. 최종 합격", "6. 불합격"],
    candidates: [
      { name: "오세훈", position: "백엔드 개발자", stage: "1. 신규 지원자 수신", applied: "2026-07-16", channel: "채용사이트", rating: "", interview: "", memo: "Java/MSA 6년, 대용량 트래픽 처리 경험" },
      { name: "이서연", position: "프로덕트 디자이너", stage: "2. 서류 합격(면접 대기)", applied: "2026-06-10", channel: "직접 지원", rating: "", interview: "2026-07-28 10:30", memo: "B2B SaaS 포트폴리오 우수 — 7/28 면접 예정" },
      { name: "김민준", position: "백엔드 개발자", stage: "3. 면접 진행", applied: "2026-06-08", channel: "채용사이트", rating: "", interview: "2026-07-24 14:00", memo: "Spring/Kotlin 5년 경력 — 7/24 1차 기술면접 예정" },
      { name: "최수아", position: "콘텐츠 마케터", stage: "4. 오퍼 제안", applied: "2026-06-03", channel: "추천", rating: "A (적극 추천)", interview: "2026-06-18 19:30", memo: "처우 협의 중 — 8/3 입사 목표" },
      { name: "박지훈", position: "백엔드 개발자", stage: "5. 최종 합격", applied: "2026-05-28", channel: "헤드헌터", rating: "B (추천)", interview: "2026-06-16 23:00", memo: "6/22 입사 완료 (백엔드 개발자)" },
      { name: "정다은", position: "인사 인턴", stage: "5. 최종 합격", applied: "2026-03-15", channel: "채용사이트", rating: "A (적극 추천)", interview: "", memo: "5/1 입사 완료" },
      { name: "한도현", position: "백엔드 개발자", stage: "6. 불합격", applied: "2026-05-20", channel: "채용사이트", rating: "D (비추천)", interview: "", memo: "경력 요건 미달" }
    ],
    positions: [
      { name: "백엔드 개발자", dept: "개발", type: "정규직", count: 2, opened: "2026-05-01", target: "2026-08-31", status: "진행중" },
      { name: "프로덕트 디자이너", dept: "디자인", type: "정규직", count: 1, opened: "2026-05-15", target: "2026-08-15", status: "진행중" },
      { name: "콘텐츠 마케터", dept: "마케팅", type: "계약직", count: 1, opened: "2026-06-01", target: "2026-08-31", status: "진행중" },
      { name: "인사 인턴", dept: "경영지원", type: "인턴", count: 1, opened: "2026-03-01", target: "2026-04-30", status: "마감" }
    ]
  }
};
