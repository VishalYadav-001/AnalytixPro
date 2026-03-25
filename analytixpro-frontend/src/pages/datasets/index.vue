<template>
  <div class="space-y-6 animate-fade-up">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="page-title">Datasets</h1>
        <p class="page-subtitle">Upload CSV / Excel files and run automated analysis.</p>
      </div>

      <div v-if="datasets.length > 0" class="flex items-center gap-3">
        <label class="btn-secondary cursor-pointer">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {{ selectedFile ? selectedFile.name : "Choose File" }}
          <input type="file" accept=".csv,.xlsx,.xls" class="hidden" @change="onFileChange" />
        </label>
        <button class="btn-primary" :disabled="uploading || !selectedFile" @click="uploadDataset">
          <svg v-if="uploading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ uploading ? "Uploading…" : "Upload" }}
        </button>
      </div>
    </div>

    <div v-if="error"   class="alert-error">{{ error }}</div>
    <div v-if="success" class="alert-success">{{ success }}</div>

    <div v-if="uploading" class="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
      <div class="h-full bg-brand-500 rounded-full animate-pulse w-2/3" />
    </div>

    <!-- Empty state -->
    <div v-if="!loading && datasets.length === 0"
         class="card-padded flex flex-col items-center justify-center py-16 text-center gap-4">
      <div class="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center">
        <svg class="w-8 h-8 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M3 5v6c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          <path d="M3 11v6c0 1.66 4 3 9 3s9-1.34 9-3v-6"/>
        </svg>
      </div>
      <div>
        <p class="font-semibold text-slate-700">No datasets yet</p>
        <p class="text-sm text-slate-400 mt-1">Upload a CSV or Excel file to get started.</p>
        <label class="btn-secondary cursor-pointer mt-4 inline-flex">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {{ selectedFile ? selectedFile.name : "Choose File" }}
          <input type="file" accept=".csv,.xlsx,.xls" class="hidden" @change="onFileChange" />
        </label>
      </div>
      <button class="btn-primary" :disabled="uploading || !selectedFile" @click="uploadDataset">
        Upload
      </button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="card h-16 skeleton"/>
    </div>

    <!-- Table -->
    <div v-if="!loading && datasets.length" class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[700px] text-sm">
          <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500 border-b border-slate-200">
            <tr>
              <th class="px-5 py-3 text-left">Name</th>
              <th class="px-5 py-3 text-left">Type</th>
              <th class="px-5 py-3 text-left">Size</th>
              <th class="px-5 py-3 text-left">Rows</th>
              <th class="px-5 py-3 text-left">Cols</th>
              <th class="px-5 py-3 text-left">Status</th>
              <th class="px-5 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="dataset in datasets" :key="dataset.id"
                class="hover:bg-slate-50/70 transition-colors">
              <td class="px-5 py-3.5">
                <span class="font-medium text-slate-800 cursor-pointer hover:text-brand-600"
                      @click="viewDataset(dataset)">
                  {{ dataset.name }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-slate-500 font-mono text-xs uppercase">
                {{ dataset.file_type || "—" }}
              </td>
              <td class="px-5 py-3.5 text-slate-500">{{ formatSize(dataset.file_size) }}</td>
              <td class="px-5 py-3.5 text-slate-600">{{ dataset.rows ?? "—" }}</td>
              <td class="px-5 py-3.5 text-slate-600">{{ dataset.columns ?? "—" }}</td>
              <td class="px-5 py-3.5">
                <span class="badge" :class="statusClass(dataset.status)">{{ dataset.status }}</span>
              </td>
              <td class="px-5 py-3.5">
                <div class="flex items-center gap-2">
                  <!--
                    PERMANENT FIX:
                    If a chat session already exists for this dataset → go to it.
                    Otherwise → create a new session.
                    Button label reflects this state clearly.
                  -->
                  <button
                    class="btn-primary btn-sm"
                    :disabled="dataset.status === 'processing' || !!sessionCreating[dataset.id]"
                    @click="handleAnalyse(dataset)"
                  >
                    <svg v-if="sessionCreating[dataset.id]" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    <!-- Show "Open Chat" if session exists, else "Analyse" -->
                    <template v-if="!sessionCreating[dataset.id]">
                      <svg v-if="getExistingSession(dataset.id)" class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                      {{ sessionCreating[dataset.id] ? "Opening…" : getExistingSession(dataset.id) ? "Open Chat" : "Analyse" }}
                    </template>
                    <template v-else>Opening…</template>
                  </button>
                  <button class="btn-secondary btn-sm" @click="viewDataset(dataset)">Details</button>
                  <button class="btn-ghost btn-sm text-red-500 hover:bg-red-50 hover:text-red-600 px-2"
                          @click="deleteDataset(dataset)" title="Delete">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                      <path d="M10 11v6"/><path d="M14 11v6"/>
                      <path d="M9 6V4h6v2"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue"
import { useRouter } from "vue-router"
import { datasetService, chatService } from "@/services/api"

const router = useRouter()

const datasets        = ref([])
const chatSessions    = ref([])   // ← holds ALL existing chat sessions
const loading         = ref(false)
const uploading       = ref(false)
const error           = ref("")
const success         = ref("")
const selectedFile    = ref(null)
const sessionCreating = reactive({}) // per-dataset loading state

// ── Helpers ────────────────────────────────────────────────────

function formatSize(bytes) {
  if (!bytes) return "—"
  const kb = bytes / 1024
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
}

function statusClass(s) {
  return {
    uploaded:   "badge-green",
    processing: "badge-amber",
    completed:  "badge-sky",
    failed:     "badge-red",
  }[s] ?? "badge-gray"
}

function onFileChange(e) {
  selectedFile.value = e.target.files?.[0] || null
}

/**
 * PERMANENT FIX — returns the existing ChatSession for a dataset if one exists.
 * Checks both `dataset` (FK id) and `dataset_id` for API shape flexibility.
 */
function getExistingSession(datasetId) {
  return chatSessions.value.find(
    s => s.dataset === datasetId || s.dataset_id === datasetId
  ) ?? null
}

// ── Data loading ────────────────────────────────────────────────

async function loadAll() {
  loading.value = true
  error.value = ""
  try {
    // Load datasets AND chat sessions in parallel — always keep sessions in sync
    const [dsRes, csRes] = await Promise.allSettled([
      datasetService.list(),
      chatService.list(),
    ])
    if (dsRes.status === "fulfilled")
      datasets.value = dsRes.value.data?.results ?? dsRes.value.data ?? []
    if (csRes.status === "fulfilled")
      chatSessions.value = csRes.value.data?.results ?? csRes.value.data ?? []
  } catch {
    error.value = "Failed to load data."
  } finally {
    loading.value = false
  }
}

// ── Actions ─────────────────────────────────────────────────────

async function uploadDataset() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ""
  success.value = ""
  try {
    await datasetService.upload({ file: selectedFile.value, name: selectedFile.value.name })
    success.value = "Dataset uploaded successfully!"
    selectedFile.value = null
    await loadAll()
  } catch (err) {
    error.value = err.response?.data?.file?.[0] ?? err.response?.data?.detail ?? "Upload failed."
  } finally {
    uploading.value = false
  }
}

/**
 * PERMANENT FIX — "Analyse" / "Open Chat" unified handler.
 *
 * Logic:
 *   1. If a chat session already exists for this dataset → navigate to it (no new session).
 *   2. If not → create a new chat session linked to this dataset → navigate to it.
 *
 * This means clicking "Analyse" a second time NEVER creates a duplicate session.
 */
async function handleAnalyse(dataset) {
  error.value = ""

  // Step 1: check local cache first (instant, no API call)
  const existing = getExistingSession(dataset.id)
  if (existing) {
    router.push(`/chat/${existing.id}`)
    return
  }

  // Step 2: re-fetch sessions from API to be absolutely sure (handles stale cache)
  sessionCreating[dataset.id] = true
  try {
    const fresh = await chatService.list()
    const freshList = fresh.data?.results ?? fresh.data ?? []
    chatSessions.value = freshList // keep local state fresh

    const freshExisting = freshList.find(
      s => s.dataset === dataset.id || s.dataset_id === dataset.id
    )
    if (freshExisting) {
      router.push(`/chat/${freshExisting.id}`)
      return
    }

    // Step 3: truly no session exists — create one
    const res = await chatService.create({ dataset: dataset.id })
    chatSessions.value.push(res.data) // update local cache
    router.push(`/chat/${res.data.id}`)

  } catch (err) {
    error.value = err.response?.data?.detail ?? "Failed to open chat."
  } finally {
    sessionCreating[dataset.id] = false
  }
}

function viewDataset(ds) {
  router.push(`/datasets/${ds.id}`)
}

async function deleteDataset(ds) {
  if (!confirm(`Delete "${ds.name}"? This cannot be undone.`)) return
  try {
    await datasetService.delete(ds.id)
    datasets.value = datasets.value.filter(d => d.id !== ds.id)
    // Also clean up any linked session from local cache
    chatSessions.value = chatSessions.value.filter(
      s => s.dataset !== ds.id && s.dataset_id !== ds.id
    )
  } catch {
    error.value = "Delete failed."
  }
}

onMounted(loadAll)
</script>