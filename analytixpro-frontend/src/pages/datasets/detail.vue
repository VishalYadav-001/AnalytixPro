<template>
  <div class="space-y-6 animate-fade-up" v-if="dataset">
    <!-- Back + header -->
    <div class="flex items-center gap-3">
      <button class="btn-ghost btn-sm" @click="$router.back()">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        Back
      </button>
    </div>

    <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <h1 class="page-title">{{ dataset.name }}</h1>
        <p class="page-subtitle">Uploaded {{ formatDate(dataset.created_at) }}</p>
      </div>
      <div class="flex gap-2">
        <button class="btn-primary" @click="runAnalysis" :disabled="analysisLoading">
          <svg v-if="analysisLoading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Run Analysis
        </button>
      </div>
    </div>

    <div v-if="error" class="alert-error">{{ error }}</div>

    <!-- Metadata cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetaCard label="File Type"  :value="(dataset.file_type || '—').toUpperCase()" />
      <MetaCard label="File Size"  :value="formatSize(dataset.file_size)" />
      <MetaCard label="Rows"       :value="dataset.rows ?? '—'" />
      <MetaCard label="Columns"    :value="dataset.columns ?? '—'" />
    </div>

    <!-- Status -->
    <div class="card-padded flex items-center gap-3">
      <span class="text-sm text-slate-500 font-medium">Status:</span>
      <span class="badge" :class="statusClass(dataset.status)">{{ dataset.status }}</span>
    </div>

    <!-- Column names -->
    <div v-if="dataset.column_names?.length" class="card-padded">
      <h2 class="font-semibold text-slate-900 mb-3 text-sm">Columns ({{ dataset.column_names.length }})</h2>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="col in dataset.column_names"
          :key="col"
          class="bg-slate-100 text-slate-700 text-xs font-mono px-2.5 py-1 rounded-lg"
        >{{ col }}</span>
      </div>
    </div>
  </div>

  <!-- Loading skeleton -->
  <div v-else-if="loading" class="space-y-5">
    <div class="skeleton h-10 w-48"/>
    <div class="grid grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="skeleton h-20"/>
    </div>
    <div class="skeleton h-32"/>
  </div>

  <div v-else class="alert-error">Dataset not found.</div>
</template>

<script setup>
import { ref, onMounted, h } from "vue"
import { useRoute, useRouter } from "vue-router"
import { datasetService, dashboardService } from "@/services/api"

const route  = useRoute()
const router = useRouter()

const dataset       = ref(null)
const loading       = ref(true)
const error         = ref("")
const analysisLoading = ref(false)

function formatDate(v) { return v ? new Date(v).toLocaleString() : "—" }
function formatSize(bytes) {
  if (!bytes) return "—"
  const kb = bytes / 1024
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
}
function statusClass(s) {
  return { uploaded:"badge-green", processing:"badge-amber", completed:"badge-sky", failed:"badge-red" }[s] ?? "badge-gray"
}

const MetaCard = {
  props: ["label", "value"],
  setup(props) {
    return () => h("div", { class: "card p-4" }, [
      h("p", { class: "text-xs text-slate-500 mb-1" }, props.label),
      h("p", { class: "font-display font-bold text-xl text-slate-900" }, props.value),
    ])
  }
}

async function load() {
  loading.value = true
  try {
    const res = await datasetService.get(route.params.id)
    dataset.value = res.data
  } catch { error.value = "Failed to load dataset." }
  finally   { loading.value = false }
}

async function runAnalysis() {
  error.value = ""
  analysisLoading.value = true
  try {
    const res   = await datasetService.runAnalysis(dataset.value.id, { analysis_type: "eda" })
    const dbRes = await dashboardService.generate(res.data.id)
    router.push(`/dashboards/${dbRes.data.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail ?? "Analysis failed."
  } finally { analysisLoading.value = false }
}

onMounted(load)
</script>
