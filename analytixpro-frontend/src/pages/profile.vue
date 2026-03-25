<template>
  <div class="max-w-2xl space-y-6 animate-fade-up">
    <div>
      <h1 class="page-title">Profile</h1>
      <p class="page-subtitle">Manage your account information and security.</p>
    </div>

    <!-- Avatar + name -->
    <div class="card p-6 flex items-center gap-5">
      <div class="w-16 h-16 rounded-2xl bg-brand-100 flex items-center justify-center shrink-0">
        <span class="font-display font-bold text-2xl text-brand-700">{{ initials }}</span>
      </div>
      <div>
        <p class="font-semibold text-lg text-slate-900">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</p>
        <p class="text-sm text-slate-500">@{{ auth.user?.username }}</p>
        <p class="text-sm text-slate-400">{{ auth.user?.email }}</p>
      </div>
    </div>

    <!-- Profile form -->
    <div class="card-padded">
      <h2 class="font-semibold text-slate-900 mb-5">Account Details</h2>

      <div v-if="profileSuccess" class="alert-success mb-4">{{ profileSuccess }}</div>
      <div v-if="profileError"   class="alert-error   mb-4">{{ profileError }}</div>

      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <BaseInput
            id="first-name"
            v-model="profileForm.first_name"
            label="First Name"
            placeholder="Jane"
            :error="profileErrors.first_name"
          />
          <BaseInput
            id="last-name"
            v-model="profileForm.last_name"
            label="Last Name"
            placeholder="Doe"
            :error="profileErrors.last_name"
          />
        </div>
        <BaseInput
          id="username"
          v-model="profileForm.username"
          label="Username"
          placeholder="jane_doe"
          :error="profileErrors.username"
        />
        <BaseInput
          id="email"
          v-model="profileForm.email"
          label="Email"
          type="email"
          placeholder="jane@company.com"
          :error="profileErrors.email"
        />
      </div>

      <div class="flex justify-end mt-6">
        <button class="btn-primary" :disabled="savingProfile" @click="saveProfile">
          <svg v-if="savingProfile" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ savingProfile ? "Saving…" : "Save Changes" }}
        </button>
      </div>
    </div>

    <!-- Change password -->
    <div class="card-padded">
      <h2 class="font-semibold text-slate-900 mb-5">Change Password</h2>

      <div v-if="pwSuccess" class="alert-success mb-4">{{ pwSuccess }}</div>
      <div v-if="pwError"   class="alert-error   mb-4">{{ pwError }}</div>

      <div class="space-y-4">
        <BaseInput
          id="old-password"
          v-model="pwForm.old_password"
          label="Current Password"
          type="password"
          placeholder="••••••••"
          :error="pwErrors.old_password"
        />
        <BaseInput
          id="new-password"
          v-model="pwForm.new_password"
          label="New Password"
          type="password"
          placeholder="Min. 8 characters"
          :error="pwErrors.new_password"
          hint="Must be at least 8 characters."
        />
      </div>

      <div class="flex justify-end mt-6">
        <button class="btn-primary" :disabled="savingPw" @click="changePassword">
          <svg v-if="savingPw" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ savingPw ? "Updating…" : "Update Password" }}
        </button>
      </div>
    </div>

    <!-- Danger zone -->
    <div class="card border-red-200 p-6">
      <h2 class="font-semibold text-red-700 mb-2">Danger Zone</h2>
      <p class="text-sm text-slate-500 mb-4">Once you log out, you will need your credentials to sign back in.</p>
      <button class="btn-danger btn-sm" @click="logout">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        Sign Out
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { authService } from "@/services/api"
import BaseInput from "@/components/BaseInput.vue"

const auth   = useAuthStore()
const router = useRouter()

const initials = computed(() => {
  const u = auth.user
  if (!u) return "?"
  if (u.first_name && u.last_name) return (u.first_name[0] + u.last_name[0]).toUpperCase()
  return (u.username?.[0] || "?").toUpperCase()
})

// ── Profile form ──────────────────────────────────────────────
const profileForm = reactive({ first_name: "", last_name: "", username: "", email: "" })
const profileErrors  = reactive({ first_name: "", last_name: "", username: "", email: "" })
const savingProfile  = ref(false)
const profileSuccess = ref("")
const profileError   = ref("")

onMounted(() => {
  const u = auth.user
  if (u) {
    profileForm.first_name = u.first_name ?? ""
    profileForm.last_name  = u.last_name  ?? ""
    profileForm.username   = u.username   ?? ""
    profileForm.email      = u.email      ?? ""
  }
})

async function saveProfile() {
  profileSuccess.value = ""
  profileError.value   = ""
  savingProfile.value  = true
  try {
    await authService.updateMe({ ...profileForm })
    await auth.fetchMe()
    profileSuccess.value = "Profile updated successfully."
  } catch (err) {
    const d = err.response?.data
    if (d && typeof d === "object") {
      Object.keys(d).forEach(k => { if (profileErrors[k] !== undefined) profileErrors[k] = d[k]?.[0] ?? d[k] })
    }
    profileError.value = "Failed to save profile."
  } finally { savingProfile.value = false }
}

// ── Password form ─────────────────────────────────────────────
const pwForm    = reactive({ old_password: "", new_password: "" })
const pwErrors  = reactive({ old_password: "", new_password: "" })
const savingPw  = ref(false)
const pwSuccess = ref("")
const pwError   = ref("")

async function changePassword() {
  pwSuccess.value = ""
  pwError.value   = ""
  pwErrors.old_password = ""
  pwErrors.new_password = ""

  if (!pwForm.old_password) { pwErrors.old_password = "Required."; return }
  if (pwForm.new_password.length < 8) { pwErrors.new_password = "Min. 8 characters."; return }

  savingPw.value = true
  try {
    await authService.changePassword({ ...pwForm })
    pwSuccess.value  = "Password changed successfully."
    pwForm.old_password = ""
    pwForm.new_password = ""
  } catch (err) {
    const d = err.response?.data
    pwErrors.old_password = d?.old_password?.[0] ?? ""
    pwErrors.new_password = d?.new_password?.[0] ?? ""
    pwError.value = d?.detail ?? "Failed to change password."
  } finally { savingPw.value = false }
}

function logout() {
  auth.logout()
  router.replace("/auth/login")
}
</script>
