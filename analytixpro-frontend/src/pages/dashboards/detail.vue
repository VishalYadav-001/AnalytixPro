<template>
  <div class="min-h-screen bg-slate-50" v-if="dashboard">

    <!-- ── Sticky Top Nav ───────────────────────────────────── -->
    <div class="sticky top-0 z-20 bg-white border-b border-slate-200 px-4 md:px-8 py-3.5
                flex items-center justify-between gap-4">
      <div class="flex items-center gap-2.5 min-w-0">
        <button class="flex items-center gap-1.5 text-slate-500 hover:text-slate-900
                       text-sm font-medium transition-colors shrink-0"
                @click="$router.push('/dashboards')">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          <span class="hidden sm:inline">Dashboards</span>
        </button>
        <span class="text-slate-300 hidden sm:inline">/</span>
        <h1 class="text-slate-900 font-bold text-sm truncate max-w-[180px] md:max-w-sm">
          {{ dashboard.title }}
        </h1>
        <span class="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full"
              :class="dashboard.level === 'advanced' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-500'">
          {{ dashboard.level }}
        </span>
      </div>
      <div class="relative shrink-0" ref="exportDropRef">
        <button @click="exportOpen = !exportOpen" :disabled="!!exportLoading"
                class="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-700
                       text-white text-xs font-bold transition-all disabled:opacity-50 shadow-sm">
          <svg v-if="exportLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          {{ exportLoading || 'Export' }}
          <svg class="w-3 h-3 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <Transition name="dd">
          <div v-if="exportOpen"
               class="absolute right-0 top-full mt-2 w-48 bg-white border border-slate-200
                      rounded-xl shadow-xl z-30 overflow-hidden py-1">
            <button v-for="opt in EXPORT_OPTIONS" :key="opt.fmt" @click="doExport(opt.fmt)"
                    class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors">
              <span class="text-base w-5 text-center">{{ opt.icon }}</span>
              <div class="text-left">
                <div class="font-semibold text-xs text-slate-800">{{ opt.label }}</div>
                <div class="text-[10px] text-slate-400">{{ opt.desc }}</div>
              </div>
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ── Page Body ─────────────────────────────────────────── -->
    <div class="max-w-screen-xl mx-auto px-4 md:px-8 py-8 space-y-10">

      <!-- Alerts -->
      <div v-if="error" class="flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm font-medium">
        <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        {{ error }}
      </div>
      <div v-if="exportSuccess" class="flex items-center gap-3 bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl text-sm font-medium">
        <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
        {{ exportSuccess }}
      </div>

      <!-- Meta row -->
      <div class="flex flex-wrap items-center gap-4 text-xs text-slate-500 font-medium -mt-4">
        <span class="flex items-center gap-1.5">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v6c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 11v6c0 1.66 4 3 9 3s9-1.34 9-3v-6"/></svg>
          {{ dashboard.dataset_name }}
        </span>
        <span class="flex items-center gap-1.5">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          {{ formatDate(dashboard.created_at) }}
        </span>
      </div>

      <!-- ══ SECTION 1 — KPI Metric Cards (full width) ══ -->
      <section v-if="kpiList.length">
        <SectionLabel title="Key Metrics"  />
        <div class="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <div v-for="(kpi, i) in kpiList" :key="kpi.column"
               class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition-shadow">
            <div class="flex items-start justify-between mb-3">
              <p class="text-[11px] font-semibold text-slate-500 truncate leading-tight max-w-[75%]">{{ kpi.column }}</p>
              <div class="w-7 h-7 rounded-lg flex items-center justify-center text-sm shrink-0"
                   :style="{ background: PALETTE[i % PALETTE.length] + '18', color: PALETTE[i % PALETTE.length] }">
                {{ KPI_ICONS[i % KPI_ICONS.length] }}
              </div>
            </div>
            <p class="text-2xl font-black text-slate-900 tracking-tight leading-none">{{ fmt(kpi.mean) }}</p>
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5 mb-3">avg</p>
            <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-2">
              <div class="h-full rounded-full"
                   :style="{ width: rangePercent(kpi) + '%', background: PALETTE[i % PALETTE.length] }"/>
            </div>
            <div class="flex justify-between text-[10px] font-mono text-slate-400">
              <span>↓ {{ fmt(kpi.min) }}</span>
              <span>↑ {{ fmt(kpi.max) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ══ SECTION 2 — Bar Chart + Pie Chart (2-col) ══ -->
      <section v-if="numColumns.length || catColumns.length">
        <SectionLabel title="Distribution Overview"  />
        <div class="mt-4 grid md:grid-cols-2 gap-6">
          <!-- Bar chart: first numeric column -->
          <div v-if="numColumns.length" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <p class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-0.5">{{ numColumns[0] }}</p>
            <p class="text-[10px] text-slate-400 mb-5">Min / Mean / Median / Max / Std breakdown</p>
            <div class="h-60 relative"><canvas ref="overviewBarEl"/></div>
          </div>
          <!-- Doughnut: first categorical column -->
          <div v-if="catColumns.length" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <p class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-0.5">{{ catColumns[0] }}</p>
            <p class="text-[10px] text-slate-400 mb-5">Top categories by frequency</p>
            <div class="h-60 relative"><canvas ref="overviewPieEl"/></div>
          </div>
        </div>
      </section>

      <!-- ══ SECTION 3 — Correlation Heatmap (full width) ══ -->
      <section>
        <SectionLabel title="Correlation Heatmap" />
        <div class="mt-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div v-if="corrCols.length">
            <div class="overflow-auto">
              <table class="border-collapse mx-auto text-[11px]">
                <thead>
                  <tr>
                    <th class="p-1.5 w-20"/>
                    <th v-for="col in corrCols" :key="col" class="p-1.5 text-center font-mono font-semibold text-slate-500">
                      <span class="block truncate max-w-[60px]" :title="col">{{ col.length > 7 ? col.slice(0,6)+'…' : col }}</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in corrCols" :key="row">
                    <td class="p-1.5 font-mono font-semibold text-slate-600 text-right pr-3 truncate max-w-[80px]" :title="row">
                      {{ row.length > 8 ? row.slice(0,7)+'…' : row }}
                    </td>
                    <td v-for="col in corrCols" :key="col" class="p-1">
                      <div class="w-14 h-10 rounded-lg flex items-center justify-center font-mono font-bold text-[11px]
                                  transition-transform hover:scale-110 cursor-default"
                           :style="corrStyle(analysis.correlation_matrix[row]?.[col])"
                           :title="`${row} × ${col}: ${formatCorr(analysis.correlation_matrix[row]?.[col])}`">
                        {{ formatCorr(analysis.correlation_matrix[row]?.[col]) }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- Heatmap legend -->
            <div class="flex items-center justify-center gap-8 mt-6 text-[10px] font-medium text-slate-500">
              <div class="flex items-center gap-1.5">
                <div class="w-10 h-3 rounded" style="background:rgba(239,68,68,0.8)"/>
                <span>−1 (negative)</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-10 h-3 rounded bg-slate-100"/>
                <span>0 (none)</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-10 h-3 rounded" style="background:rgba(59,130,246,0.8)"/>
                <span>+1 (positive)</span>
              </div>
            </div>
          </div>
          <div v-else class="h-40 flex items-center justify-center text-slate-400 text-sm">
            No numeric columns available for correlation analysis.
          </div>
        </div>
      </section>

      <!-- ══ SECTION 4 — Missing Values + Summary Stats (2-col) ══ -->
      <section>
        <SectionLabel title="Data Quality & Summary" />
        <div class="mt-4 grid md:grid-cols-2 gap-6">
          <!-- Missing Values bar chart -->
          <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <p class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-5">Missing Values</p>
            <div v-if="hasMissing" class="h-56 relative"><canvas ref="missingChartEl"/></div>
            <div v-else class="h-56 flex flex-col items-center justify-center gap-3">
              <div class="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center text-2xl">✅</div>
              <p class="font-bold text-emerald-700 text-sm">No missing values!</p>
              <p class="text-xs text-slate-400">Your dataset is 100% complete.</p>
            </div>
          </div>
          <!-- Summary stats mini table -->
          <div v-if="analysis?.summary_statistics" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 overflow-hidden">
            <p class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4">Summary Statistics</p>
            <div class="overflow-auto max-h-56">
              <table class="w-full text-[11px]">
                <thead>
                  <tr class="border-b border-slate-100">
                    <th class="pb-2 text-left font-bold text-slate-500 text-[10px] uppercase tracking-wider">Column</th>
                    <th v-for="s in coreStatKeys" :key="s"
                        class="pb-2 text-right font-bold text-slate-500 text-[10px] uppercase tracking-wider px-2">
                      {{ s }}
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-50">
                  <tr v-for="(stats, col) in analysis.summary_statistics" :key="col"
                      class="hover:bg-slate-50/60 transition-colors">
                    <td class="py-2 font-mono font-semibold text-slate-700 truncate max-w-[100px]" :title="col">{{ col }}</td>
                    <td v-for="s in coreStatKeys" :key="s" class="py-2 px-2 text-right font-mono text-slate-500">
                      {{ formatStat(stats[s]) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <!-- ══ SECTION 5 — All Categorical Charts (3-col grid) ══ -->
      <section v-if="catColumns.length">
        <SectionLabel title="Categorical Distributions" />
        <div class="mt-4 grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div v-for="col in catColumns" :key="col"
               class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <p class="text-xs font-bold text-slate-700 font-mono mb-0.5 truncate">{{ col }}</p>
            <p class="text-[10px] text-slate-400 mb-4">{{ getCatEntries(col).length }} categories</p>
            <div class="h-52 relative"><canvas :ref="el => setCatRef(col, el)"/></div>
          </div>
        </div>
      </section>

      <!-- ══ SECTION 6 — All Numeric KPI Bar Charts (2-col grid) ══ -->
      <section v-if="numColumns.length">
        <SectionLabel title="Numeric Column Analysis" />
        <div class="mt-4 grid md:grid-cols-2 gap-5">
          <div v-for="(col, i) in numColumns" :key="col"
               class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <p class="text-xs font-bold text-slate-700 font-mono mb-0.5 truncate">{{ col }}</p>
            <p class="text-[10px] text-slate-400 mb-4">
              Avg: <span class="font-semibold text-slate-700">{{ fmt(analysis.top_kpis[col]?.mean) }}</span>
              &nbsp;·&nbsp;
              Std: <span class="font-semibold text-slate-700">{{ fmt(analysis.top_kpis[col]?.std) }}</span>
            </p>
            <div class="h-48 relative"><canvas :ref="el => setNumRef(col, el)"/></div>
          </div>
        </div>
      </section>

    </div>
  </div>

  <!-- Loading skeleton -->
  <div v-else-if="loading" class="max-w-screen-xl mx-auto px-4 md:px-8 py-10 space-y-8">
    <div class="h-8 w-56 bg-slate-200 rounded-xl animate-pulse"/>
    <div class="grid grid-cols-5 gap-4">
      <div v-for="i in 5" :key="i" class="h-32 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
    <div class="grid grid-cols-2 gap-6">
      <div class="h-72 bg-slate-200 rounded-2xl animate-pulse"/>
      <div class="h-72 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
    <div class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
    <div class="grid grid-cols-2 gap-6">
      <div class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
      <div class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
    <div class="grid grid-cols-3 gap-5">
      <div v-for="i in 3" :key="i" class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
  </div>

  <div v-else class="max-w-screen-xl mx-auto px-8 py-20 text-center text-slate-400 text-sm">
    Dashboard not found.
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, defineComponent, h } from "vue"
import { useRoute } from "vue-router"
import { dashboardService } from "@/services/api"
import {
  Chart,
  BarController, BarElement,
  CategoryScale, LinearScale,
  DoughnutController, ArcElement,
  Tooltip, Legend,
} from "chart.js"

Chart.register(BarController, BarElement, CategoryScale, LinearScale, DoughnutController, ArcElement, Tooltip, Legend)

// ── Inline section header component ──────────────────────────
const SectionLabel = defineComponent({
  props: ["title", "icon"],
  setup(p) {
    return () => h("div", { class: "flex items-center gap-3" }, [
      h("span", { class: "text-xl leading-none" }, p.icon),
      h("h2", { class: "text-sm font-bold text-slate-800 tracking-tight" }, p.title),
      h("div", { class: "flex-1 h-px bg-slate-200" }),
    ])
  },
})

// ── Constants ─────────────────────────────────────────────────
const PALETTE = [
  "#3b82f6","#8b5cf6","#10b981","#f59e0b","#ef4444",
  "#06b6d4","#84cc16","#ec4899","#f97316","#14b8a6",
]
const KPI_ICONS = ["📈","💰","🎯","⚡","🔥","📦","🏆","💎","🌟","📐"]
const EXPORT_OPTIONS = [
  { fmt: "pdf",   icon: "📄", label: "PDF Report",       desc: "Formatted printable report" },
  { fmt: "ipynb", icon: "📓", label: "Jupyter Notebook", desc: "Interactive Python notebook" },
  { fmt: "py",    icon: "🐍", label: "Python Script",    desc: "Standalone runnable script"  },
]
const BASE_OPTS = { responsive: true, maintainAspectRatio: false, animation: { duration: 500 } }

// ── State ──────────────────────────────────────────────────────
const route         = useRoute()
const dashboard     = ref(null)
const analysis      = ref(null)
const loading       = ref(true)
const error         = ref("")
const exportLoading = ref("")
const exportSuccess = ref("")
const exportOpen    = ref(false)
const exportDropRef = ref(null)

const missingChartEl = ref(null)
const overviewBarEl  = ref(null)
const overviewPieEl  = ref(null)
const catRefs        = {}
const numRefs        = {}
const charts         = []

function setCatRef(col, el) { if (el) catRefs[col] = el }
function setNumRef(col, el) { if (el) numRefs[col] = el }

// ── Computed ───────────────────────────────────────────────────
const kpiList = computed(() => {
  const k = analysis.value?.top_kpis
  return k ? Object.entries(k).map(([column, vals]) => ({ column, ...vals })) : []
})
const corrCols = computed(() => {
  const cm = analysis.value?.correlation_matrix
  return cm ? Object.keys(cm) : []
})
const catColumns = computed(() => {
  const ci = analysis.value?.categorical_insights
  return ci ? Object.keys(ci) : []
})
const numColumns = computed(() => {
  const k = analysis.value?.top_kpis
  return k ? Object.keys(k) : []
})
const hasMissing = computed(() => {
  const m = analysis.value?.missing_values?.count
  return m && Object.values(m).some(v => v > 0)
})
const coreStatKeys = computed(() => {
  const s = analysis.value?.summary_statistics
  if (!s) return []
  const allKeys = Object.keys(Object.values(s)[0] || {})
  const preferred = ["count", "mean", "std", "min", "max"]
  const found = preferred.filter(k => allKeys.includes(k))
  return found.length ? found : allKeys.slice(0, 5)
})

// ── Formatters ─────────────────────────────────────────────────
function fmt(v) {
  if (v === null || v === undefined) return "—"
  const n = parseFloat(v)
  if (isNaN(n)) return String(v)
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
  if (Math.abs(n) >= 1_000)     return n.toLocaleString("en", { maximumFractionDigits: 1 })
  return n.toFixed(2)
}
function formatStat(v) {
  if (v === null || v === undefined || v === "") return "—"
  if (typeof v === "number") return Number.isInteger(v) ? v : v.toFixed(3)
  return v
}
function formatCorr(v) {
  if (v === null || v === undefined) return "—"
  return parseFloat(v).toFixed(2)
}
function formatDate(v) {
  if (!v) return "—"
  return new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}
function corrStyle(v) {
  if (v === null || v === undefined) return { background: "#f8fafc", color: "#94a3b8" }
  const val = parseFloat(v), abs = Math.abs(val)
  if (abs < 0.05) return { background: "#f8fafc", color: "#94a3b8" }
  if (val > 0) return { background: `rgba(59,130,246,${0.15 + abs * 0.65})`, color: abs > 0.55 ? "#fff" : "#1d4ed8" }
  return { background: `rgba(239,68,68,${0.15 + abs * 0.65})`, color: abs > 0.55 ? "#fff" : "#b91c1c" }
}
function getCatEntries(col) {
  return Object.entries(analysis.value?.categorical_insights?.[col] || {}).slice(0, 8)
}
function rangePercent(kpi) {
  const range = (kpi.max ?? 0) - (kpi.min ?? 0)
  if (!range) return 50
  return Math.round(Math.max(5, Math.min(95, ((kpi.mean ?? 0) - (kpi.min ?? 0)) / range * 100)))
}

// ── Chart builders ─────────────────────────────────────────────
function destroyCharts() { charts.forEach(c => c.destroy()); charts.length = 0 }

function buildMissingChart() {
  const m = analysis.value?.missing_values?.count
  if (!m || !missingChartEl.value) return
  const entries = Object.entries(m).filter(([, v]) => v > 0)
  if (!entries.length) return
  charts.push(new Chart(missingChartEl.value, {
    type: "bar",
    data: {
      labels: entries.map(([k]) => k),
      datasets: [{ label: "Missing", data: entries.map(([, v]) => v),
        backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length] + "cc"),
        borderRadius: 8, borderSkipped: false }],
    },
    options: { ...BASE_OPTS, plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
        y: { grid: { color: "#f1f5f9" }, ticks: { color: "#94a3b8", font: { size: 10 } }, beginAtZero: true },
      } },
  }))
}

function buildOverviewBar() {
  if (!numColumns.value.length || !overviewBarEl.value) return
  const col = numColumns.value[0]
  const kpi = analysis.value?.top_kpis?.[col]
  if (!kpi) return
  charts.push(new Chart(overviewBarEl.value, {
    type: "bar",
    data: {
      labels: ["Min", "Mean", "Median", "Max", "Std Dev"],
      datasets: [{ label: col, data: [kpi.min, kpi.mean, kpi.median, kpi.max, kpi.std],
        backgroundColor: ["#3b82f620","#3b82f6cc","#3b82f680","#3b82f630","#8b5cf660"],
        borderColor: PALETTE[0], borderWidth: 1.5, borderRadius: 10, borderSkipped: false }],
    },
    options: { ...BASE_OPTS,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${fmt(ctx.parsed.y)}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#94a3b8", font: { size: 11 } } },
        y: { grid: { color: "#f1f5f9" }, ticks: { color: "#94a3b8", font: { size: 11 } } },
      } },
  }))
}

function buildOverviewPie() {
  if (!catColumns.value.length || !overviewPieEl.value) return
  const entries = getCatEntries(catColumns.value[0])
  charts.push(new Chart(overviewPieEl.value, {
    type: "doughnut",
    data: {
      labels: entries.map(([k]) => k),
      datasets: [{ data: entries.map(([, v]) => v), backgroundColor: PALETTE, borderWidth: 3, borderColor: "#fff", hoverOffset: 10 }],
    },
    options: { ...BASE_OPTS,
      plugins: { legend: { display: true, position: "right",
        labels: { font: { size: 10 }, color: "#64748b", boxWidth: 10, padding: 8 } } },
      cutout: "60%" },
  }))
}

function buildCatCharts() {
  if (!analysis.value?.categorical_insights) return
  catColumns.value.forEach(col => {
    const el = catRefs[col]
    if (!el) return
    const entries = getCatEntries(col)
    charts.push(new Chart(el, {
      type: "doughnut",
      data: {
        labels: entries.map(([k]) => k),
        datasets: [{ data: entries.map(([, v]) => v), backgroundColor: PALETTE, borderWidth: 3, borderColor: "#fff", hoverOffset: 8 }],
      },
      options: { ...BASE_OPTS,
        plugins: { legend: { display: true, position: "right",
          labels: { font: { size: 10 }, color: "#64748b", boxWidth: 10, padding: 6 } } },
        cutout: "58%" },
    }))
  })
}

function buildNumCharts() {
  const kpis = analysis.value?.top_kpis
  if (!kpis) return
  numColumns.value.forEach((col, i) => {
    const el = numRefs[col]
    if (!el) return
    const s = kpis[col]
    if (!s) return
    const c = PALETTE[i % PALETTE.length]
    charts.push(new Chart(el, {
      type: "bar",
      data: {
        labels: ["Min", "Mean", "Median", "Max", "Std"],
        datasets: [{ label: col, data: [s.min, s.mean, s.median, s.max, s.std],
          backgroundColor: [`${c}20`,`${c}cc`,`${c}80`,`${c}30`,`${c}50`],
          borderColor: c, borderWidth: 1.5, borderRadius: 8, borderSkipped: false }],
      },
      options: { ...BASE_OPTS,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${fmt(ctx.parsed.y)}` } } },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
          y: { grid: { color: "#f8fafc" }, ticks: { color: "#94a3b8", font: { size: 10 } } },
        } },
    }))
  })
}

async function buildAllCharts() {
  await nextTick()
  destroyCharts()
  buildMissingChart()
  buildOverviewBar()
  buildOverviewPie()
  buildCatCharts()
  buildNumCharts()
}

// ── Load ───────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const res = await dashboardService.get(route.params.id)
    dashboard.value = res.data
    analysis.value  = res.data.analysis ?? null
    await buildAllCharts()
  } catch {
    error.value = "Failed to load dashboard."
  } finally {
    loading.value = false
  }
}

// ── Export ─────────────────────────────────────────────────────
async function doExport(format) {
  exportOpen.value = false; error.value = ""; exportSuccess.value = ""
  exportLoading.value = format.toUpperCase()
  try {
    const res = await dashboardService.export(route.params.id, format)
    const url = res.data.file_url
    if (url) { window.open(url, "_blank"); exportSuccess.value = `${format.toUpperCase()} export ready!` }
    else exportSuccess.value = "Export queued successfully."
  } catch (err) {
    error.value = err.response?.data?.detail ?? "Export failed."
  } finally {
    exportLoading.value = ""
  }
}

function onOutsideClick(e) {
  if (exportDropRef.value && !exportDropRef.value.contains(e.target)) exportOpen.value = false
}

onMounted(() => { load(); document.addEventListener("click", onOutsideClick) })
onUnmounted(() => { destroyCharts(); document.removeEventListener("click", onOutsideClick) })
</script>

<style scoped>
.dd-enter-active, .dd-leave-active { transition: all .15s ease; }
.dd-enter-from, .dd-leave-to       { opacity: 0; transform: translateY(-6px); }
</style>