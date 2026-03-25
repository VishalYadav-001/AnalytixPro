<template>
  <div class="space-y-6 animate-fade-up">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="page-title">AI Chat</h1>
        <p class="page-subtitle">Let the AI guide your data analysis step by step.</p>
      </div>
      <button class="btn-primary" @click="newSession">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        New Chat
      </button>
    </div>

    <div v-if="error" class="alert-error">{{ error }}</div>

    <!-- Empty -->
    <div v-if="!loading && sessions.length === 0"
         class="card-padded flex flex-col items-center py-16 gap-4 text-center">
      <div class="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center">
        <svg class="w-8 h-8 text-brand-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <div>
        <p class="font-semibold text-slate-700">No chat sessions yet</p>
        <p class="text-sm text-slate-400 mt-1">Start a new chat to begin your analysis journey.</p>
      </div>
      <button class="btn-primary" @click="newSession">Start your first chat →</button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="card h-20 skeleton"/>
    </div>

    <!-- Session list -->
    <div v-if="!loading && sessions.length" class="space-y-3">
      <div v-for="s in sessions" :key="s.id"
           class="card p-4 flex items-center justify-between gap-4 hover:shadow-md transition-shadow cursor-pointer"
           @click="openSession(s)">
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
               :class="s.is_complete ? 'bg-emerald-50' : 'bg-brand-50'">
            <svg class="w-5 h-5" :class="s.is_complete ? 'text-emerald-500' : 'text-brand-500'"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div>
            <p class="font-medium text-slate-800 text-sm">
              {{ s.dataset_name ? `Analysis: ${s.dataset_name}` : `Session #${s.id}` }}
            </p>
            <p class="text-xs text-slate-400 mt-0.5">
              {{ s.message_count ?? 0 }} messages · {{ formatDate(s.created_at) }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="badge" :class="s.is_complete ? 'badge-green' : 'badge-blue'">
            {{ s.is_complete ? "Complete" : "Active" }}
          </span>
          <svg class="w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- New session modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showModal = false"/>
          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-fade-up">
            <h2 class="font-display font-bold text-lg text-slate-900 mb-1">New Chat Session</h2>
            <p class="text-sm text-slate-500 mb-5">Choose a dataset to analyse, or start without one.</p>

            <div class="space-y-4">
              <div>
                <label class="label">Select Dataset (optional)</label>

                <!--
                  PERMANENT FIX: Only show datasets that do NOT already have a chat session.
                  Datasets with existing sessions are excluded to prevent duplicate sessions.
                -->
                <select class="input-base" v-model="newSessionDataset"
                        :disabled="availableDatasets.length === 0 && datasets.length > 0">
                  <option value="">— No dataset —</option>
                  <option v-for="ds in availableDatasets" :key="ds.id" :value="ds.id">
                    {{ ds.name }}
                  </option>
                </select>

                <!-- Hint when all datasets are already analysed -->
                <div v-if="datasets.length > 0 && availableDatasets.length === 0"
                     class="mt-2 flex items-center gap-2 text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  <svg class="w-3.5 h-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  All datasets already have a chat session.
                  <button class="underline font-semibold" @click="showModal = false">View existing chats ↑</button>
                </div>

                <!-- Show how many datasets are already taken -->
                <p v-else-if="datasets.length > availableDatasets.length"
                   class="mt-1.5 text-xs text-slate-400">
                  {{ datasets.length - availableDatasets.length }} dataset(s) already have active sessions.
                </p>
              </div>
            </div>

            <div class="flex gap-3 mt-6">
              <button class="btn-secondary flex-1" @click="showModal = false">Cancel</button>
              <button class="btn-primary flex-1" @click="createSession" :disabled="creating">
                <svg v-if="creating" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ creating ? "Creating…" : "Start Chat" }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { chatService, datasetService } from "@/services/api"

const router = useRouter()

const sessions          = ref([])
const datasets          = ref([])
const loading           = ref(false)
const error             = ref("")
const showModal         = ref(false)
const newSessionDataset = ref("")
const creating          = ref(false)

function formatDate(v) {
  return v ? new Date(v).toLocaleDateString() : "—"
}

/**
 * PERMANENT FIX — filter out datasets that already have a chat session.
 * Uses both `dataset` and `dataset_id` to handle different API shapes.
 */
const availableDatasets = computed(() => {
  const usedIds = new Set(
    sessions.value
      .map(s => s.dataset ?? s.dataset_id)
      .filter(id => id !== null && id !== undefined)
  )
  return datasets.value.filter(ds => !usedIds.has(ds.id))
})

async function load() {
  loading.value = true
  try {
    const [s, d] = await Promise.allSettled([
      chatService.list(),
      datasetService.list(),
    ])
    if (s.status === "fulfilled") sessions.value = s.value.data?.results ?? s.value.data ?? []
    if (d.status === "fulfilled") datasets.value = d.value.data?.results ?? d.value.data ?? []
  } catch {
    error.value = "Failed to load sessions."
  } finally {
    loading.value = false
  }
}

function newSession() {
  newSessionDataset.value = ""
  showModal.value = true
}

function openSession(s) {
  router.push(`/chat/${s.id}`)
}

async function createSession() {
  creating.value = true
  error.value = ""
  try {
    const payload = newSessionDataset.value ? { dataset: newSessionDataset.value } : {}
    const res = await chatService.create(payload)
    sessions.value.unshift(res.data) // add to top of list
    showModal.value = false
    router.push(`/chat/${res.data.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail ?? "Failed to create session."
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: all .2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>