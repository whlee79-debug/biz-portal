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
    ? { rev: "#3987e5", cost: "#e66767", profit: "#199e70", aux: "#c98500",
        ink: "#ffffff", ink2: "#c3c2b7", muted: "#898781", grid: "#2c2c2a", surface: "#1a1a19" }
    : { rev: "#2a78d6", cost: "#e34948", profit: "#1baf7a", aux: "#eda100",
        ink: "#0b0b0b", ink2: "#52514e", muted: "#898781", grid: "#e1e0d9", surface: "#fcfcfb" };
})();

if (window.Chart) {
  Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif';
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
          ? { beginAtZero: true, grid: { color: THEME.grid }, border: { display: false } }
          : { stacked: !!o.stacked, grid: { display: false }, border: { color: THEME.grid } },
        y: o.horizontal
          ? { grid: { display: false }, border: { color: THEME.grid } }
          : { stacked: !!o.stacked, beginAtZero: true, grid: { color: THEME.grid }, border: { display: false } }
      }
    }
  });
}

/* 공통 내비게이션 */
function renderNav(active) {
  const tabs = [
    ["index.html", "종합 현황"],
    ["finance.html", "재무"],
    ["people.html", "인력·조직"],
    ["recruiting.html", "채용"]
  ];
  const el = document.createElement("nav");
  el.innerHTML = `<div class="inner">
    <a class="brand" href="/">🏠 포털</a>
    ${tabs.map(([href, label]) =>
      `<a class="tab${active === href ? " active" : ""}" href="${href}">${label}</a>`).join("")}
    <span class="spacer"></span>
    <a class="tab" href="/chatbot/">💬 HR 챗봇</a>
  </div>`;
  document.body.prepend(el);
}
