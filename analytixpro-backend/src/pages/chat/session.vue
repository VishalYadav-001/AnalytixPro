<template>
  <div class="h-dvh flex flex-col lg:flex-row bg-slate-50 overflow-hidden relative">

    <!-- Mobile tab bar -->
    <div class="flex lg:hidden border-b border-slate-200 bg-white shrink-0 z-10">
      <button @click="activeTab = 'chat'"
              class="flex-1 py-3.5 text-[10px] font-black uppercase tracking-widest transition-all"
              :class="activeTab === 'chat' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-slate-400'">
        Chat
      </button>
      <button @click="activeTab = 'data'"
              class="flex-1 py-3.5 text-[10px] font-black uppercase tracking-widest transition-all"
              :class="activeTab === 'data' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-slate-400'">
        Dataset
      </button>
    </div>

    <!-- ── Left: Chat Panel ──────────────────────────────────────────── -->
    <div class="flex flex-col lg:w-[460px] xl:w-[500px] shrink-0 bg-white border-r border-slate-100 h-full transition-all"
         :class="activeTab === 'chat' ? 'flex' : 'hidden lg:flex'">

      <!-- Chat header -->
      <div class="px-5 py-3.5 border-b border-slate-100 flex items-center gap-3 shrink-0 bg-white">
        <div class="flex-1 min-w-0">
          <h1 class="font-bold text-slate-900 text-sm truncate">
            {{ session?.dataset_name ?? 'Analytics Setup' }}
          </h1>
          <div class="flex items-center gap-2 mt-0.5">
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                    :class="session?.is_complete ? 'bg-emerald-400' : 'bg-indigo-400'"/>
              <span class="relative inline-flex rounded-full h-2 w-2"
                    :class="session?.is_complete ? 'bg-emerald-500' : 'bg-indigo-500'"/>
            </span>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-tight">
              {{ session?.is_complete ? 'Configuration Complete' : `Question ${currentStep} of ${STEPS.length}` }}
            </p>
          </div>
        </div>
        <!-- Step progress dots -->
        <div class="flex gap-1.5">
          <div v-for="i in STEPS.length" :key="i"
               class="h-1.5 rounded-full transition-all duration-300"
               :class="i <= currentStep
                 ? 'bg-indigo-500 w-4'
                 : 'bg-slate-200 w-1.5'"/>
        </div>
      </div>

      <!-- Messages -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar">
        <!-- Loading skeleton -->
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

            <!-- Avatar -->
            <div class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-[11px] font-bold border transition-transform hover:scale-105"
                 :class="msg.role === 'user'
                   ? 'bg-indigo-600 text-white border-indigo-600'
                   : 'bg-white text-indigo-500 border-slate-200'">
              {{ msg.role === 'user' ? initials : '🤖' }}
            </div>

            <!-- Bubble -->
            <div class="max-w-[88%] space-y-2">
              <div class="px-4 py-3 rounded-2xl text-[13px] leading-relaxed"
                   :class="msg.role === 'user'
                     ? 'bg-indigo-600 text-white rounded-tr-none shadow-sm shadow-indigo-200'
                     : 'bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200/60'">
                <div v-html="renderMessage(msg.content)" class="prose-chat select-text"/>
              </div>

              <!-- Quick reply chips (for last assistant message) -->
              <div v-if="!session?.is_complete && !sending && msg === lastAssistantMessage && quickReplies.length"
                   class="flex flex-wrap gap-1.5 pt-1">
                <button v-for="opt in quickReplies" :key="opt"
                        @click="sendQuickReply(opt)"
                        class="px-3.5 py-1.5 text-[11px] font-semibold rounded-full bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 active:scale-95 transition-all shadow-sm">
                  {{ opt }}
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Input area -->
      <div class="p-4 border-t border-slate-100 bg-white shrink-0 pb-[max(1rem,env(safe-area-inset-bottom))]">

        <!-- Completed: action buttons -->
        <div v-if="session?.is_complete" class="space-y-2.5">
          <button v-if="dashboardId" @click="router.push(`/dashboards/${dashboardId}`)"
                  class="w-full bg-indigo-600 active:scale-[0.98] text-white py-3.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-200">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Open Dashboard
          </button>
          <div v-else class="flex items-center justify-center gap-3 p-4 bg-indigo-50 rounded-xl border border-indigo-100 text-indigo-600 text-xs font-bold">
            <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-20"/>
              <path d="M4 12a8 8 0 018-8" stroke="currentColor" stroke-width="4"/>
            </svg>
            Building your dashboard...
          </div>
        </div>

        <!-- Active: text input -->
        <div v-else class="relative">
          <textarea v-model="input" ref="inputEl" rows="1"
                    placeholder="Type your answer..."
                    @keydown.enter.exact.prevent="sendMessage"
                    class="w-full bg-slate-100 border-none rounded-xl px-4 py-3 pr-14 text-sm focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all resize-none max-h-32"/>
          <button @click="sendMessage" :disabled="!input?.trim() || sending"
                  class="absolute right-2.5 bottom-2.5 w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center disabled:bg-slate-300 transition-all shadow-md active:scale-90">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- ── Right: Data Preview Panel ────────────────────────────────── -->
    <div class="flex-1 overflow-y-auto bg-slate-50 h-full transition-all"
         :class="activeTab === 'data' ? 'block' : 'hidden lg:block'">
      <div class="max-w-3xl mx-auto p-5 md:p-8 space-y-5 pb-24 lg:pb-8">

        <!-- Config summary card -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
            <h3 class="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400">Your Dashboard Setup</h3>
            <span v-if="session?.is_complete" class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
              ✓ Ready
            </span>
            <span v-else class="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
              Step {{ currentStep }} / {{ STEPS.length }}
            </span>
          </div>
          <div class="p-5 grid grid-cols-2 gap-5">
            <div v-for="field in configFields" :key="field.key" class="space-y-1">
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-tight flex items-center gap-1.5">
                <span>{{ field.icon }}</span>{{ field.label }}
              </span>
              <p class="text-xs font-bold truncate"
                 :class="session?.[field.key] ? 'text-slate-900' : 'text-slate-300 italic'">
                {{ session?.[field.key] ? formatFieldValue(field.key, session[field.key]) : 'Awaiting...' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Dataset stats -->
        <div v-if="dataset" class="grid grid-cols-3 gap-3">
          <div v-for="stat in datasetStats" :key="stat.label"
               class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{{ stat.label }}</p>
            <p class="text-lg font-black text-slate-900 mt-0.5">{{ stat.val || '—' }}</p>
          </div>
        </div>

        <!-- Column browser -->
        <div v-if="dataset?.column_names" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black uppercase tracking-[0.15em] text-slate-500">
              Dataset Columns
              <span class="ml-1.5 text-slate-400 font-normal normal-case">{{ dataset.column_names.length }} total</span>
            </h3>
            <span class="text-[10px] text-slate-400 italic hidden sm:inline">Click to use in chat</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <button v-for="col in dataset.column_names" :key="col"
                    @click="useColumnName(col)"
                    class="px-3 py-1.5 rounded-lg border border-slate-100 bg-slate-50 text-slate-600 text-[11px] font-mono hover:border-indigo-400 hover:text-indigo-700 hover:bg-indigo-50 active:scale-95 transition-all truncate max-w-[150px]">
              {{ col }}
            </button>
          </div>
        </div>

        <!-- Tips card -->
        <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-5">
          <h3 class="text-[10px] font-black uppercase tracking-widest text-indigo-600 mb-3">💡 Tips</h3>
          <ul class="space-y-2 text-[11px] text-slate-600">
            <li class="flex gap-2"><span class="text-indigo-400 font-bold shrink-0">→</span> Type **sales**, **hr**, **financial**, or **custom** for the data type</li>
            <li class="flex gap-2"><span class="text-indigo-400 font-bold shrink-0">→</span> Click any column name above to paste it into your answer</li>
            <li class="flex gap-2"><span class="text-indigo-400 font-bold shrink-0">→</span> Type **none** if you don't have a specific target metric</li>
            <li class="flex gap-2"><span class="text-indigo-400 font-bold shrink-0">→</span> Choose **advanced** for deeper analytics and all charts</li>
          </ul>
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
const activeTab       = ref("chat")
const session         = ref(null)
const messages        = ref([])
const dataset         = ref(null)
const loadingSession  = ref(true)
const sending         = ref(false)
const isInitializing  = ref(false)
const input           = ref("")
const messagesEl      = ref(null)
const inputEl         = ref(null)
const dashboardId     = ref(null)
const generatingDashboard = ref(false)

const STEPS = [
  { key: "analysis_type", label: "Domain" },
  { key: "goal",          label: "Goal" },
  { key: "target_column", label: "Primary Metric" },
  { key: "dashboard_level", label: "Detail Level" },
  { key: "download_code", label: "Export Code" },
]

const QUICK_REPLY_MAP = {
  analysis_type:   ["Sales", "HR", "Financial", "Custom"],
  goal:            ["Find Trends", "Predict Outcomes", "Custom"],
  dashboard_level: ["Basic", "Advanced"],
  download_code:   ["Yes", "No"],
}

const configFields = [
  { key: "analysis_type",   label: "Domain",       icon: "🏷️" },
  { key: "goal",            label: "Goal",         icon: "🎯" },
  { key: "target_column",   label: "Primary KPI",  icon: "📊" },
  { key: "dashboard_level", label: "Detail Level", icon: "⚙️" },
]

// Computed
const currentStep = computed(() => {
  if (!session.value) return 1
  for (let i = 0; i < STEPS.length; i++) {
    const val = session.value[STEPS[i].key]
    if (val === null || val === undefined || val === "") return i + 1
  }
  return STEPS.length
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

const initials = computed(() =>
  (auth.user?.username?.[0] || "U").toUpperCase()
)

const visibleMessages = computed(() =>
  messages.value.filter(m => m.content !== "__init__")
)

const datasetStats = computed(() => {
  if (!dataset.value) return []
  return [
    { label: "Rows",       val: dataset.value.rows?.toLocaleString() },
    { label: "Columns",    val: dataset.value.columns },
    { label: "File Size",  val: formatSize(dataset.value.file_size) },
  ]
})

// Methods
function formatSize(bytes) {
  if (!bytes) return "0 KB"
  const kb = bytes / 1024
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
}

function formatFieldValue(key, val) {
  if (key === "download_code") return val ? "Yes" : "No"
  if (key === "target_column") return val === "__none__" ? "All metrics" : String(val)
  return String(val).replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
}

function renderMessage(content) {
  if (!content) return ""
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>')
    .replace(/\n/g, "<br>")
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

function useColumnName(col) {
  input.value += (input.value ? " " : "") + col
  activeTab.value = "chat"
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

  const originalInput = text
  input.value = ""
  sending.value = true

  const tempId = Date.now()
  messages.value.push({ id: tempId, role: "user", content: text })
  await scrollToBottom()

  try {
    const res = await chatService.sendMessage(route.params.id, { content: text })
    messages.value = messages.value.filter(m => m.id !== tempId)
    if (res.data.user_message)      messages.value.push(res.data.user_message)
    if (res.data.assistant_message) messages.value.push(res.data.assistant_message)

    await loadSession()
    if (session.value.is_complete) await checkOrBuildDashboard()
  } catch (e) {
    messages.value = messages.value.filter(m => m.id !== tempId)
    input.value = originalInput
    console.error("Send error:", e)
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

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
      if (id) { dashboardId.value = id; return }
    }
    await buildDashboardPipeline()
  } catch {
    await buildDashboardPipeline()
  }
}

onMounted(loadSession)
watch(messages, scrollToBottom)
</script>

<style scoped>
.prose-chat br { content: ""; display: block; margin: 0.4rem 0; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
.h-dvh { height: 100dvh; }
</style>
