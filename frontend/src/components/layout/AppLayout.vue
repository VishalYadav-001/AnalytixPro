<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden relative">

    <Transition name="fade">
      <div
        v-if="sidebarOpen"
        @click="sidebarOpen = false"
        class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 md:hidden"
      />
    </Transition>

    <aside
      class="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col transition-transform duration-300 ease-in-out md:relative md:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="h-16 flex items-center justify-between px-5 border-b border-slate-100">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shrink-0">
            <svg viewBox="0 0 24 24" class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="font-display font-bold text-slate-900 text-lg">AnalytixPro</span>
        </div>
        <button @click="sidebarOpen = false" class="md:hidden p-1 text-slate-400 hover:text-slate-600 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        <RouterLink
          v-for="link in navigation"
          :key="link.to"
          :to="link.to"
          @click="sidebarOpen = false"
          class="nav-link"
          :class="isActive(link.to) ? 'nav-link-active' : ''"
        >
          <div v-html="link.icon" class="w-5 h-5 shrink-0" />
          <span>{{ link.name }}</span>
        </RouterLink>
      </nav>

      <div class="border-t border-slate-100 p-3 mb-16 md:mb-0">
        <div
          class="flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors"
          @click="goProfile"
        >
          <div class="w-9 h-9 rounded-full bg-brand-100 flex items-center justify-center border border-brand-200 shrink-0">
            <span class="text-brand-700 text-xs font-bold">{{ initials }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-slate-900 truncate">{{ auth.user?.username || 'User' }}</p>
          </div>
          <button
            @click.stop="logout"
            class="text-slate-400 hover:text-red-500 p-1 transition-colors"
            title="Sign out"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <header class="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-8 z-30 shrink-0">
        <button class="md:hidden p-2 text-slate-600" @click="sidebarOpen = true">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        <div class="flex-1 px-4">
          <h2 class="text-sm font-bold text-slate-800 uppercase tracking-wider">{{ currentPageName }}</h2>
        </div>

        <div class="hidden sm:flex flex-col items-end">
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{{ greeting }}</span>
          <span class="text-sm font-semibold text-slate-700">{{ auth.user?.first_name || auth.user?.username }}</span>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto bg-slate-50/50 pb-20 md:pb-0 scrollbar-thin">
        <div class="max-w-7xl mx-auto px-4 py-6">
          <RouterView />
        </div>
      </main>
    </div>

    <div
      v-if="!sidebarOpen"
      class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-6 py-3 flex justify-between items-center md:hidden z-40"
    >
      <RouterLink
        v-for="link in navigation"
        :key="link.to"
        :to="link.to"
        class="flex flex-col items-center gap-1 transition-colors"
        :class="isActive(link.to) ? 'text-brand-600' : 'text-slate-400'"
      >
        <div v-html="link.icon" class="w-5 h-5" />
        <span class="text-[10px] font-semibold">{{ link.name }}</span>
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { RouterView, RouterLink, useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const auth        = useAuthStore()
const router      = useRouter()
const route       = useRoute()
const sidebarOpen = ref(false)

const navigation = [
  {
    name: "Overview",
    to: "/home",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  },
  {
    name: "Datasets",
    to: "/datasets",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v6c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 11v6c0 1.66 4 3 9 3s9-1.34 9-3v-6"/></svg>`,
  },
  {
    name: "AI Chat",
    to: "/chat",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
  },
  {
    name: "Dashboards",
    to: "/dashboards",
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  },
]

const isActive = (path) => route.path.startsWith(path)

const currentPageName = computed(() => {
  const map = { home: "Overview", datasets: "Datasets", "dataset-detail": "Dataset Detail", chat: "AI Chat", "chat-detail": "AI Chat", dashboards: "Dashboards", "dashboard-detail": "Dashboard", profile: "Profile" }
  return map[route.name] ?? ""
})

const initials = computed(() => {
  const u = auth.user
  if (!u) return "?"
  return (u.username?.[0] || "U").toUpperCase()
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return "Good morning"
  if (h < 17) return "Good afternoon"
  return "Good evening"
})

function logout() {
  auth.logout()
  router.push("/auth/login")
}

function goProfile() {
  sidebarOpen.value = false
  router.push("/profile")
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
