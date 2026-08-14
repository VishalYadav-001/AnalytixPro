<template>
  <div class="space-y-6 animate-fade-up">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="page-title">Dashboards</h1>
        <p class="page-subtitle">View and export AI-generated dashboards from your datasets.</p>
      </div>
    </div>

    <div v-if="error" class="alert-error">{{ error }}</div>

    <!-- Empty -->
    <div v-if="!loading && dashboards.length === 0" class="card-padded flex flex-col items-center py-16 gap-4 text-center">
      <div class="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
      </div>
      <div>
        <p class="font-semibold text-slate-700">No dashboards yet</p>
        <p class="text-sm text-slate-400 mt-1 max-w-xs">
          Run an analysis on a dataset to automatically generate a dashboard.
        </p>
      </div>
      <button class="btn-primary" @click="$router.push('/datasets')">Upload a Dataset →</button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="grid md:grid-cols-2 gap-5">
      <div v-for="i in 4" :key="i" class="card h-44 skeleton"/>
    </div>

    <!-- Grid -->
    <div v-if="!loading && dashboards.length" class="grid md:grid-cols-2 gap-5">
      <div
        v-for="db in dashboards"
        :key="db.id"
        class="card p-5 hover:shadow-md transition-shadow group"
      >
        <!-- Title row -->
        <div class="flex items-start justify-between gap-3 mb-4">
          <div class="min-w-0">
            <h2 class="font-semibold text-slate-900 truncate group-hover:text-brand-600 transition-colors cursor-pointer"
                @click="viewDashboard(db)">
              {{ db.title }}
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ db.dataset_name }} · {{ formatDate(db.created_at) }}
            </p>
          </div>
          <span class="badge shrink-0" :class="db.level === 'advanced' ? 'badge-blue' : 'badge-gray'">
            {{ db.level }}
          </span>
        </div>

        <!-- Mini chart placeholder -->
        <div class="h-16 rounded-xl bg-gradient-to-r from-brand-50 to-blue-50 flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-brand-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-2">
          <button class="btn-primary btn-sm flex-1" @click="viewDashboard(db)">
            View Dashboard
          </button>
          <div class="relative" ref="exportMenuRef">
            <button
              class="btn-secondary btn-sm"
              @click="toggleExportMenu(db.id)"
            >
              Export
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            <!-- Dropdown -->
            <Transition name="dropdown">
              <div v-if="openExportMenu === db.id"
                class="absolute right-0 bottom-full mb-1 w-40 bg-white border border-slate-200 rounded-xl shadow-lg z-10 overflow-hidden">
                <button
                  v-for="fmt in ['pdf','ipynb','py']" :key="fmt"
                  class="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  @click="exportDashboard(db, fmt)"
                  :disabled="exportLoading[db.id]"
                >
                  <svg class="w-3.5 h-3.5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  {{ { pdf: 'PDF Report', ipynb: 'Jupyter Notebook', py: 'Python Script' }[fmt] }}
                </button>
              </div>
            </Transition>
          </div>
          <button
            class="btn-ghost btn-sm text-red-500 hover:bg-red-50 px-2"
            @click="deleteDashboard(db)"
            title="Delete"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
              <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
            </svg>
          </button>
        </div>

        <!-- Export loading indicator -->
        <div v-if="exportLoading[db.id]" class="mt-3 flex items-center gap-2 text-xs text-slate-500">
          <svg class="animate-spin w-3.5 h-3.5 text-brand-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Generating export…
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { dashboardService } from "@/services/api"

const router = useRouter()

const dashboards    = ref([])
const loading       = ref(false)
const error         = ref("")
const openExportMenu = ref(null)
const exportLoading  = reactive({})

function formatDate(v) {
  return v ? new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"
}

async function load() {
  loading.value = true
  error.value = ""
  try {
    const res = await dashboardService.list()
    dashboards.value = res.data?.results ?? res.data ?? []
  } catch { error.value = "Failed to load dashboards." }
  finally   { loading.value = false }
}

function viewDashboard(db) { router.push(`/dashboards/${db.id}`) }

function toggleExportMenu(id) {
  openExportMenu.value = openExportMenu.value === id ? null : id
}

async function exportDashboard(db, fmt) {
  openExportMenu.value = null
  exportLoading[db.id] = true
  try {
    const res = await dashboardService.export(db.id, fmt)
    const url = res.data.file_url
    if (url) window.open(url, "_blank")
  } catch (err) {
    error.value = err.response?.data?.detail ?? "Export failed."
  } finally { exportLoading[db.id] = false }
}

async function deleteDashboard(db) {
  if (!confirm(`Delete dashboard "${db.title}"? This cannot be undone.`)) return
  try {
    await dashboardService.delete(db.id)
    dashboards.value = dashboards.value.filter(d => d.id !== db.id)
  } catch { error.value = "Delete failed." }
}

// Close dropdown on outside click
function onClickOutside(e) {
  if (openExportMenu.value !== null) openExportMenu.value = null
}

onMounted(() => { load(); document.addEventListener("click", onClickOutside) })
onUnmounted(() => document.removeEventListener("click", onClickOutside))
</script>

<style scoped>
.dropdown-enter-active, .dropdown-leave-active { transition: all .15s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(6px); }
</style>
