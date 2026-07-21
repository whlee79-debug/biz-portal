/* 공통: 테마 감지 + Chart.js 기본 설정 + 렌더 헬퍼 */
(function () {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  function applyTheme() {
    document.documentElement.setAttribute("data-theme", mq.matches ? "dark" : "light");
  }
  applyTheme();
  mq.addEventListener("change", () => location.reload());
})();

const THEME = (function () {
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  return dark
    ? { rev: "#3987e5", cost: "#e66767", profit: "#22c55e", aux: "#c98500",
        ink: "#f3f4f6", ink2: "#9ca3af", muted: "#6b7280", grid: "#242830", surface: "#171a1f" }
    : { rev: "#2a78d6", cost: "#e34948", profit: "#16a34a", aux: "#eda100",
        ink: "#111827", ink2: "#6b7280", muted: "#9ca3af", grid: "#eef0f2", surface: "#ffffff" };
})();

if (window.Chart) {
  Chart.defaults.font.family = '"Inter", "Pretendard", system-ui, -apple-system, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif';
  Chart.defaults.font.size = 12.5;
  Chart.defaults.color = THEME.muted;
  Chart.defaults.borderColor = THEME.grid;
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.plugins.legend.labels.boxHeight = 10;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.pointStyle = "circle";
  Chart.defaults.plugins.legend.labels.color = THEME.ink2;
  Chart.defaults.plugins.tooltip.backgroundColor = THEME.surface;
  Chart.defaults.plugins.tooltip.titleColor = THEME.ink;
  Chart.defaults.plugins.tooltip.bodyColor = THEME.ink2;
  Chart.defaults.plugins.tooltip.borderColor = THEME.grid;
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
}

/* 라인 끝점에 시리즈명 직접 라벨 (범례 보조 — CVD 대비) */
const endLabelPlugin = {
  id: "endLabel",
  afterDatasetsDraw(chart, args, opts) {
    if (!opts || !opts.enabled) return;
    const { ctx } = chart;
    chart.data.datasets.forEach((ds, i) => {
      const meta = chart.getDatasetMeta(i);
      if (meta.hidden || meta.type !== "line" || !meta.data.length) return;
      const last = meta.data[meta.data.length - 1];
      ctx.save();
      ctx.font = "600 11.5px system-ui, sans-serif";
      ctx.fillStyle = ds.borderColor;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(ds.label, last.x + 8, last.y);
      ctx.restore();
    });
  }
};
if (window.Chart) Chart.register(endLabelPlugin);

function lineDS(label, data, color, fill) {
  return {
    label, data, borderColor: color, backgroundColor: color,
    borderWidth: 2, pointRadius: 0, pointHoverRadius: 5,
    pointHoverBackgroundColor: color, pointHoverBorderColor: THEME.surface,
    pointHoverBorderWidth: 2, tension: 0.3, fill: fill || false
  };
}

function makeLineChart(id, labels, datasets, opts) {
  const o = opts || {};
  return new Chart(document.getElementById(id), {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      layout: { padding: { right: o.endLabels ? 64 : 8 } },
      plugins: {
        legend: { display: datasets.length > 1, position: "top", align: "end" },
        endLabel: { enabled: !!o.endLabels },
        tooltip: { callbacks: { label: c => ` ${c.dataset.label}: ${c.parsed.y.toLocaleString()}${o.unit || ""}` } }
      },
      scales: {
        x: { grid: { display: false }, border: { color: THEME.grid } },
        y: {
          beginAtZero: !!o.zero, grid: { color: THEME.grid }, border: { display: false },
          ticks: { callback: v => v.toLocaleString() }
        }
      }
    }
  });
}

function makeBarChart(id, labels, datasets, opts) {
  const o = opts || {};
  datasets.forEach(ds => {
    ds.borderRadius = 4;
    ds.borderSkipped = false;
    ds.maxBarThickness = o.thickness || 26;
    if (o.stacked) { ds.borderColor = THEME.surface; ds.borderWidth = 2; }
  });
  return new Chart(document.getElementById(id), {
    type: "bar",
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: o.horizontal ? "y" : "x",
      plugins: {
        legend: { display: datasets.length > 1, position: "top", align: "end" },
        tooltip: { callbacks: { label: c => ` ${c.dataset.label}: ${(o.horizontal ? c.parsed.x : c.parsed.y).toLocaleString()}${o.unit || ""}` } }
      },
      scales: {
        x: o.horizontal
          ? { beginAtZero: true, grid: { color: THEME.grid }, border: { display: false }, ticks: { precision: 0 } }
          : { stacked: !!o.stacked, grid: { display: false }, border: { color: THEME.grid } },
        y: o.horizontal
          ? { grid: { display: false }, border: { color: THEME.grid } }
          : { stacked: !!o.stacked, beginAtZero: true, grid: { color: THEME.grid }, border: { display: false }, ticks: { precision: 0 } }
      }
    }
  });
}

/* 공통 사이드바 내비게이션 */
function renderNav(active) {
  const I = {
    home: '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20h14V9.5"/></svg>',
    chart: '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V4"/><path d="M4 20h16"/><path d="M8 16v-4"/><path d="M13 16V8"/><path d="M18 16v-6"/></svg>',
    coin: '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>',
    people: '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0"/><path d="M16 5.5a3.2 3.2 0 0 1 0 6"/><path d="M17 14.5a5.5 5.5 0 0 1 3.5 5.5"/></svg>',
    target: '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="0.6" fill="currentColor" stroke="none"/></svg>',
    chat: '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M20 15a2 2 0 0 1-2 2H8l-4 4V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z"/></svg>'
  };
  const tabs = [
    ["index.html", "종합 현황", I.chart],
    ["finance.html", "재무", I.coin],
    ["people.html", "인력·조직", I.people],
    ["recruiting.html", "채용", I.target]
  ];
  const el = document.createElement("aside");
  el.className = "sidebar";
  el.innerHTML = `
    <a class="brand" href="/">
      <span class="logo">◆</span>
      <span><b>Biz Portal</b><small>Executive Dashboard</small></span>
    </a>
    <nav class="side-nav">
      ${tabs.map(([href, label, icon]) =>
        `<a class="${active === href ? "active" : ""}" href="${href}">${icon}<span>${label}</span></a>`).join("")}
    </nav>
    <div class="side-foot">
      <a href="/chatbot/">${I.chat}<span class="ftxt">HR 챗봇</span></a>
      <a href="/">${I.home}<span class="ftxt">포털 홈</span></a>
    </div>`;
  document.body.prepend(el);
}
