<template>
  <div class="h-dvh flex flex-col lg:flex-row bg-white lg:bg-slate-50 overflow-hidden relative">
    
    <div class="flex lg:hidden border-b border-slate-200 bg-white shrink-0 z-10">
      <button 
        @click="activeTab = 'chat'"
        class="flex-1 py-4 text-[10px] font-black uppercase tracking-widest transition-all"
        :class="activeTab === 'chat' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/30' : 'text-slate-400'"
      >
        Chat Flow
      </button>
      <button 
        @click="activeTab = 'data'"
        class="flex-1 py-4 text-[10px] font-black uppercase tracking-widest transition-all"
        :class="activeTab === 'data' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/30' : 'text-slate-400'"
      >
        Data Preview
      </button>
    </div>

    <div 
      class="flex flex-col flex-1 min-w-0 lg:max-w-[480px] border-r border-slate-100 bg-white transition-all duration-300 h-full"
      :class="activeTab === 'chat' ? 'flex' : 'hidden lg:flex'"
    >
      <div class="px-4 py-3 border-b border-slate-100 flex items-center gap-3 shrink-0 bg-white">
        <div class="flex-1 min-w-0">
          <h1 class="font-bold text-slate-900 text-sm truncate">
            {{ session?.dataset_name ?? "Analysis Chat" }}
          </h1>
          <div class="flex items-center gap-2 mt-0.5">
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" :class="session?.is_complete ? 'bg-emerald-400' : 'bg-indigo-400'"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" :class="session?.is_complete ? 'bg-emerald-500' : 'bg-indigo-500'"></span>
            </span>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-tight">
              {{ session?.is_complete ? "Configuration Ready" : `Step ${currentStep} of 5` }}
            </p>
          </div>
        </div>
        
        <div class="flex gap-1">
          <div v-for="i in 5" :key="i" 
               class="h-1 w-3 rounded-full transition-all"
               :class="i <= currentStep ? 'bg-indigo-500' : 'bg-slate-200'"></div>
        </div>
      </div>

      <div ref="messagesEl" class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth custom-scrollbar">
        <template v-if="loadingSession">
          <div v-for="i in 3" :key="i" class="flex gap-3 animate-pulse">
            <div class="w-8 h-8 rounded-full bg-slate-100 shrink-0"/>
            <div class="flex-1 space-y-2 mt-1">
              <div class="h-3 bg-slate-100 rounded w-3/4"/>
              <div class="h-3 bg-slate-100 rounded w-1/2"/>
            </div>
          </div>
        </template>

        <template v-else>
          <div v-for="msg in visibleMessages" :key="msg.id" 
               class="flex gap-3" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
            <div class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-[10px] font-bold border active:scale-90 transition-transform"
                 :class="msg.role === 'user' ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-400 border-slate-200'">
              {{ msg.role === 'user' ? initials : 'AI' }}
            </div>

            <div class="max-w-[85%] space-y-2">
              <div class="px-4 py-2.5 rounded-2xl text-[13px] leading-relaxed shadow-sm"
                   :class="msg.role === 'user' 
                     ? 'bg-indigo-600 text-white rounded-tr-none' 
                     : 'bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200'">
                <div v-html="renderMessage(msg.content)" class="prose-chat select-text"/>
              </div>

              <div v-if="!session?.is_complete && !sending && msg === lastAssistantMessage && quickReplies.length" 
                   class="flex flex-wrap gap-2 pt-1">
                <button v-for="opt in quickReplies" :key="opt"
                        @click="sendQuickReply(opt)"
                        class="px-4 py-2 text-xs font-bold rounded-full bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 active:scale-95 transition-all shadow-sm">
                  {{ opt }}
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="p-4 border-t border-slate-100 bg-white shrink-0 pb-[max(1rem,env(safe-area-inset-bottom))]">
        <div v-if="session?.is_complete" class="space-y-3">
          <button v-if="dashboardId" @click="router.push(`/dashboards/${dashboardId}`)"
                  class="w-full bg-emerald-600 active:scale-[0.98] text-white py-4 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-100">
            Open Analytics Dashboard
          </button>
          <div v-else class="flex items-center justify-center gap-3 p-4 bg-slate-50 rounded-xl border border-dashed border-slate-300 text-slate-500 text-[10px] font-bold uppercase tracking-widest">
            <svg class="animate-spin w-4 h-4 text-indigo-500" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-20"/><path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4"/></svg>
            Building Pipeline...
          </div>
        </div>

        <div v-else class="relative group">
          <textarea
            v-model="input"
            ref="inputEl"
            rows="1"
            placeholder="Type your message..."
            @keydown.enter.exact.prevent="sendMessage"
            class="w-full bg-slate-100 border-none rounded-2xl px-4 py-3.5 pr-14 text-sm focus:ring-2 focus:ring-indigo-500/20 transition-all resize-none max-h-32"
          />
          <button 
            @click="sendMessage"
            :disabled="!input?.trim() || sending"
            class="absolute right-2 bottom-2 p-2.5 rounded-xl bg-indigo-600 text-white disabled:bg-slate-300 transition-all shadow-md active:scale-90"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </div>
    </div>

    <div 
      class="flex-1 overflow-y-auto bg-slate-50 transition-all duration-300 h-full"
      :class="activeTab === 'data' ? 'block' : 'hidden lg:block'"
    >
      <div class="max-w-4xl mx-auto p-4 md:p-8 space-y-6 pb-24 lg:pb-8">
        
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
            <h3 class="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400">Analysis Summary</h3>
            <span class="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">Live Build</span>
          </div>
          <div class="p-5 grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div v-for="field in configFields" :key="field.key" class="space-y-1">
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-tight">{{ field.label }}</span>
              <p class="text-xs md:text-sm font-black truncate" :class="session?.[field.key] ? 'text-slate-900' : 'text-slate-300 italic'">
                {{ session?.[field.key] ? formatFieldValue(field.key, session[field.key]) : 'Awaiting...' }}
              </p>
            </div>
          </div>
        </div>

        <div v-if="dataset" class="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
          <div v-for="stat in [
            { label: 'Total Rows', val: dataset.rows?.toLocaleString(), icon: 'rows' },
            { label: 'Data Points', val: (dataset.rows * dataset.columns)?.toLocaleString(), icon: 'points' },
            { label: 'File Size', val: formatSize(dataset.file_size), icon: 'size' }
          ]" :key="stat.label" class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center gap-3 md:gap-4">
            <div class="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 shrink-0">
              <svg v-if="stat.icon==='rows'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M3 10h18M3 14h18m-9-4v8m-3-8v8m6-8v8M3 6h18a2 2 0 012 2v8a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2z"/></svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            </div>
            <div class="min-w-0">
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{{ stat.label }}</p>
              <p class="text-sm md:text-lg font-black text-slate-900 truncate">{{ stat.val || '—' }}</p>
            </div>
          </div>
        </div>

        <div v-if="dataset?.column_names" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 md:p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black uppercase tracking-[0.15em] text-slate-500">Available Columns</h3>
            <span class="text-[10px] text-slate-400 italic hidden sm:inline">Tap to use in chat</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button 
              v-for="col in dataset.column_names" :key="col"
              @click="useColumnName(col)"
              class="px-3 py-2 rounded-lg border border-slate-100 bg-slate-50 text-slate-600 text-[11px] font-mono hover:border-indigo-500 hover:text-indigo-700 hover:bg-white active:scale-95 transition-all truncate max-w-[150px]"
            >
              {{ col }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { chatService, datasetService, dashboardService, analysisService } from "@/services/api"
import { useAuthStore } from "@/stores/auth"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// State
const activeTab = ref('chat')
const session = ref(null)
const messages = ref([])
const dataset = ref(null)
const loadingSession = ref(true)
const sending = ref(false)
const isInitializing = ref(false) // GUARD: Prevents double welcome calls
const input = ref("")
const messagesEl = ref(null)
const inputEl = ref(null)
const dashboardId = ref(null)
const generatingDashboard = ref(false)

// Constants
const STEPS = [
  { key: "analysis_type", label: "Analysis Type" },
  { key: "goal", label: "Goal" },
  { key: "target_column", label: "Target Column" },
  { key: "dashboard_level", label: "Dashboard Level" },
  { key: "download_code", label: "Export Code" },
]

const QUICK_REPLY_MAP = {
  analysis_type: ["Sales", "HR", "Financial", "Marketing"],
  goal: ["Find Trends", "Predict Outcomes", "Identify Outliers"],
  dashboard_level: ["Basic", "Advanced"],
  download_code: ["Yes", "No"],
}

const configFields = [
  { key: "analysis_type", label: "Type" },
  { key: "goal", label: "Goal" },
  { key: "target_column", label: "Target" },
  { key: "dashboard_level", label: "UI Level" },
]

// Computed
const currentStep = computed(() => {
  if (!session.value) return 1
  for (let i = 0; i < STEPS.length; i++) {
    const val = session.value[STEPS[i].key]
    if (val === null || val === undefined || val === "") return i + 1
  }
  return 5
})

const lastAssistantMessage = computed(() =>
  [...messages.value].reverse().find(m => m.role === "assistant") ?? null
)

const quickReplies = computed(() => {
  if (session.value?.is_complete || sending.value) return []
  const step = STEPS[currentStep.value - 1]
  if (!step) return []
  const val = session.value?.[step.key]
  if (val !== null && val !== undefined && val !== "") return []
  return QUICK_REPLY_MAP[step.key] ?? []
})

const initials = computed(() => {
  return (auth.user?.username?.[0] || 'U').toUpperCase()
})

const visibleMessages = computed(() =>
  messages.value.filter(m => m.content !== "__init__")
)

// Methods
function formatSize(bytes) {
  if (!bytes) return "0 KB"
  const kb = bytes / 1024
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
}

function formatFieldValue(key, val) {
  if (key === "download_code") return val ? "Yes" : "No"
  return String(val).replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
}

function renderMessage(content) {
  if (!content) return ""
  return content
    .replace(/\*\*(.*?)\*\*/g, '<b class="font-bold text-slate-900">$1</b>')
    .replace(/\n/g, "<br>")
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

function useColumnName(col) {
  input.value += (input.value ? ' ' : '') + col
  activeTab.value = 'chat'
  nextTick(() => inputEl.value?.focus())
}

async function loadSession() {
  loadingSession.value = true
  try {
    const [sessRes, msgsRes] = await Promise.all([
      chatService.get(route.params.id),
      chatService.messages(route.params.id),
    ])
    session.value = sessRes.data
    messages.value = msgsRes.data?.results ?? msgsRes.data ?? []

    if (session.value.dataset) {
      const dsRes = await datasetService.get(session.value.dataset)
      dataset.value = dsRes.data
    }

    if (session.value.is_complete) await checkOrBuildDashboard()

    const hasAssistant = messages.value.some(m => m.role === "assistant")
    if (!hasAssistant && !isInitializing.value) await triggerWelcome()
    
    await scrollToBottom()
  } catch (e) {
    console.error(e)
  } finally {
    loadingSession.value = false
  }
}

async function triggerWelcome() {
  if (isInitializing.value) return
  isInitializing.value = true
  sending.value = true
  try {
    const res = await chatService.sendMessage(route.params.id, { content: "__init__" })
    session.value = { ...res.data.session }
    const existing = messages.value.filter(m => m.content !== "__init__")
    const assistant = res.data.assistant_message
    messages.value = assistant ? [...existing, assistant] : existing
  } finally {
    sending.value = false
    isInitializing.value = false
    await scrollToBottom()
  }
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || sending.value) return
  
  // 1. Lock the UI and clear input
  const originalInput = text
  input.value = ""
  sending.value = true

  // 2. Optimistic Update: Show the user's message immediately
  const tempId = Date.now()
  const tempMsg = { id: tempId, role: "user", content: text }
  messages.value.push(tempMsg)
  await scrollToBottom()

  try {
    // 3. Send to Backend
    const res = await chatService.sendMessage(route.params.id, { content: text })
    
    // 4. Replace the temporary message with the real one from DB
    messages.value = messages.value.filter(m => m.id !== tempId)
    
    if (res.data.user_message) {
       messages.value.push(res.data.user_message)
    }
    
    // 5. Push the NEW Assistant message
    if (res.data.assistant_message) {
      messages.value.push(res.data.assistant_message)
    }

    // 6. Reload the session to ensure state is up-to-date (fixes potential backend sync issues)
    await loadSession()

    // 7. Handle Dashboard completion if needed (now that session is reloaded)
    if (session.value.is_complete) {
      await checkOrBuildDashboard()
    }

  } catch (e) {
    // Rollback on error
    messages.value = messages.value.filter(m => m.id !== tempId)
    input.value = originalInput // Give the text back to the user
    console.error("Critical Send Error:", e)
  } finally {
    // 8. Finally unlock the UI
    sending.value = false
    await scrollToBottom()
  }
}

// FIX: Added guard to prevent double-clicks on buttons
function sendQuickReply(opt) {
  if (sending.value) return
  input.value = opt
  sendMessage()
}

async function buildDashboardPipeline() {
  if (generatingDashboard.value) return
  generatingDashboard.value = true
  try {
    const analysisRes = await datasetService.runAnalysis(session.value.dataset, {
      analysis_type: "eda",
      chat_session_id: session.value.id,
    })

    const analysisId = analysisRes?.data?.id
    if (!analysisId) return

    const dbRes = await dashboardService.generate(analysisId)
    const id = dbRes?.data?.id ?? dbRes?.data?.dashboard_id
    if (id) dashboardId.value = id
  } catch (e) {
    console.error("buildDashboardPipeline error:", e)
  } finally {
    generatingDashboard.value = false
  }
}

async function checkOrBuildDashboard() {
  try {
    const analyses = await analysisService.list()
    const list = analyses.data?.results ?? analyses.data ?? []

    const linked = list.find(a =>
      a.chat_session === session.value.id ||
      a.chat_session_id === session.value.id
    )

    if (linked) {
      const id = linked.dashboard_id ?? linked.dashboard?.id
      if (id) {
        dashboardId.value = id
        return
      }
    }
    await buildDashboardPipeline()
  } catch (e) {
    console.error("checkOrBuildDashboard error:", e)
    await buildDashboardPipeline()
  }
}

onMounted(loadSession)
watch(messages, scrollToBottom)
</script>

<style scoped>
.prose-chat br { content: ""; display: block; margin: 0.5rem 0; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
.h-dvh { height: 100dvh; }
</style>