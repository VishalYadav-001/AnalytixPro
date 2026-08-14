<template>
  <div class="space-y-6 md:space-y-8 animate-fade-up px-1">
    <div>
      <h1 class="page-title text-xl md:text-2xl font-bold">Welcome back, {{ displayName }}</h1>
      <p class="page-subtitle text-sm text-slate-500">Here's a snapshot of your analytics workspace.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
      <StatCard
        label="Datasets"
        :value="stats.datasets"
        icon="database"
        color="blue"
        to="/datasets"
      />
      <StatCard
        label="Analyses Run"
        :value="stats.analyses"
        icon="activity"
        color="purple"
      />
      <StatCard
        label="Dashboards"
        :value="stats.dashboards"
        icon="bar-chart"
        color="green"
        to="/dashboards"
      />
      <StatCard
        label="Chat Sessions"
        :value="stats.chats"
        icon="message"
        color="amber"
        to="/chat"
      />
    </div>

    <div>
      <h2 class="font-display font-semibold text-lg text-slate-900 mb-4">Quick Actions</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <ActionCard
          title="Upload Dataset"
          desc="Import a CSV or Excel file to begin analysis."
          icon="upload"
          cta="Upload"
          to="/datasets"
        />
        <ActionCard
          title="Start AI Chat"
          desc="Let the AI guide you through your data questions."
          icon="bot"
          cta="New Chat"
          to="/chat"
        />
        <ActionCard
          title="View Dashboards"
          desc="Browse, export, and share your generated dashboards."
          icon="layout"
          cta="Browse"
          to="/dashboards"
        />
      </div>
    </div>

    <div v-if="recentDatasets.length">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-display font-semibold text-lg text-slate-900">Recent Datasets</h2>
        <RouterLink to="/datasets" class="text-sm text-brand-600 hover:underline font-medium">View all →</RouterLink>
      </div>
      
      <div class="card overflow-hidden">
        <div class="overflow-x-auto w-full">
          <table class="w-full text-sm whitespace-nowrap md:whitespace-normal">
            <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-4 md:px-5 py-3 text-left">Name</th>
                <th class="px-4 md:px-5 py-3 text-left">Type</th>
                <th class="px-4 md:px-5 py-3 text-left">Rows</th>
                <th class="px-4 md:px-5 py-3 text-left">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="ds in recentDatasets" :key="ds.id" class="hover:bg-slate-50 transition-colors cursor-pointer" @click="$router.push(`/datasets/${ds.id}`)">
                <td class="px-4 md:px-5 py-3 font-medium text-slate-800 truncate max-w-[150px] md:max-w-none">{{ ds.name }}</td>
                <td class="px-4 md:px-5 py-3 text-slate-500 uppercase text-xs">{{ ds.file_type }}</td>
                <td class="px-4 md:px-5 py-3 text-slate-500">{{ ds.rows ?? "—" }}</td>
                <td class="px-4 md:px-5 py-3">
                  <StatusBadge :status="ds.status" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from "vue"
import { RouterLink, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { datasetService, analysisService, dashboardService, chatService } from "@/services/api"

const auth   = useAuthStore()
const router = useRouter()

const displayName = computed(() => {
  const u = auth.user
  if (!u) return "there"
  return u.first_name || u.username
})

const stats = ref({ datasets: "—", analyses: "—", dashboards: "—", chats: "—" })
const recentDatasets = ref([])

onMounted(async () => {
  try {
    const [ds, an, db, ch] = await Promise.allSettled([
      datasetService.list(),
      analysisService.list(),
      dashboardService.list(),
      chatService.list(),
    ])
    if (ds.status === "fulfilled") {
      const data = ds.value.data?.results ?? ds.value.data
      stats.value.datasets = Array.isArray(data) ? data.length : "—"
      recentDatasets.value = (Array.isArray(data) ? data : []).slice(0, 5)
    }
    if (an.status === "fulfilled") {
      const data = an.value.data?.results ?? an.value.data
      stats.value.analyses = Array.isArray(data) ? data.length : "—"
    }
    if (db.status === "fulfilled") {
      const data = db.value.data?.results ?? db.value.data
      stats.value.dashboards = Array.isArray(data) ? data.length : "—"
    }
    if (ch.status === "fulfilled") {
      const data = ch.value.data?.results ?? ch.value.data
      stats.value.chats = Array.isArray(data) ? data.length : "—"
    }
  } catch {}
})

// ── Sub-components ───────────────────────────────────────────
const colorMap = {
  blue:   { bg: "bg-blue-50",   icon: "text-blue-600",  label: "text-blue-700" },
  purple: { bg: "bg-purple-50", icon: "text-purple-600", label: "text-purple-700" },
  green:  { bg: "bg-emerald-50",icon: "text-emerald-600",label: "text-emerald-700" },
  amber:  { bg: "bg-amber-50",  icon: "text-amber-600", label: "text-amber-700" },
}

const StatCard = {
  props: ["label", "value", "icon", "color", "to"],
  setup(props) {
    const c = colorMap[props.color] || colorMap.blue
    const icons = {
      database:   `<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v6c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 11v6c0 1.66 4 3 9 3s9-1.34 9-3v-6"/>`,
      activity:   `<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>`,
      "bar-chart":`<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>`,
      message:    `<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>`,
    }
    return () => h(
      props.to ? RouterLink : "div",
      props.to ? { to: props.to, class: "card p-4 md:p-5 flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer" }
               : { class: "card p-4 md:p-5 flex items-center gap-4" },
      [
        h("div", { class: `w-12 h-12 rounded-xl ${c.bg} flex items-center justify-center shrink-0` }, [
          h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8", class: `w-5 h-5 ${c.icon}`, innerHTML: icons[props.icon] })
        ]),
        h("div", { class: "truncate" }, [
          h("p", { class: "text-xl md:text-2xl font-display font-bold text-slate-900" }, props.value),
          h("p", { class: "text-xs text-slate-500 mt-0.5 truncate" }, props.label),
        ])
      ]
    )
  }
}

const ActionCard = {
  props: ["title", "desc", "icon", "cta", "to"],
  setup(props) {
    const icons = {
      upload: `<polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>`,
      bot:    `<circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>`,
      layout: `<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>`,
    }
    return () => h(
      "div",
      { class: "card p-5 md:p-6 flex flex-col gap-4 hover:shadow-md transition-shadow h-full" },
      [
        h("div", { class: "w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center" }, [
          h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8", class: "w-5 h-5 text-brand-600", innerHTML: icons[props.icon] })
        ]),
        h("div", {}, [
          h("h3", { class: "font-semibold text-slate-900 text-sm" }, props.title),
          h("p",  { class: "text-xs text-slate-500 mt-1 leading-relaxed" }, props.desc),
        ]),
        h(RouterLink, { to: props.to, class: "btn-primary btn-sm self-start mt-auto" }, () => props.cta + " →")
      ]
    )
  }
}

const StatusBadge = {
  props: ["status"],
  setup(props) {
    const cls = {
      uploaded:   "badge-green",
      processing: "badge-amber",
      completed:  "badge-sky",
      failed:     "badge-red",
    }
    return () => h("span", { class: `badge ${cls[props.status] ?? "badge-gray"}` }, props.status)
  }
}
</script>