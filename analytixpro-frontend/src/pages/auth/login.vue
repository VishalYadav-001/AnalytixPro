<template>
  <div class="w-full max-w-4xl bg-white rounded-3xl shadow-2xl overflow-hidden flex min-h-[580px] animate-fade-up">

    <!-- Left panel -->
    <AuthPanel />

    <!-- Right: login form -->
    <div class="flex-1 flex flex-col justify-center px-8 py-10 md:px-12">

      <!-- Tab switcher -->
      <div class="flex bg-slate-100 rounded-xl p-1 mb-8">
        <button class="tab-pill tab-pill-active" disabled>Sign In</button>
        <RouterLink to="/auth/register" class="tab-pill tab-pill-inactive ml-1">
          Create Account
        </RouterLink>
      </div>

      <div class="mb-7">
        <h1 class="font-display text-2xl font-bold text-slate-900">Welcome back</h1>
        <p class="text-brand-600 text-sm mt-1">Sign in to your AnalytixPro account.</p>
      </div>

      <!-- Error / success alerts -->
      <Transition name="alert">
        <div v-if="errorMsg" class="alert-error mb-5 flex items-start gap-2">
          <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4 mt-0.5 shrink-0 text-red-500" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {{ errorMsg }}
        </div>
      </Transition>

      <Transition name="alert">
        <div v-if="successMsg" class="alert-success mb-5">{{ successMsg }}</div>
      </Transition>

      <!-- Form -->
      <div class="space-y-4">
        <BaseInput
          id="login-username"
          v-model="form.username"
          label="Username or Email"
          placeholder="your_username"
          :error="errors.username"
          @enter="submit"
        />
        <BaseInput
          id="login-password"
          v-model="form.password"
          label="Password"
          type="password"
          placeholder="••••••••"
          :error="errors.password"
          @enter="submit"
        />
      </div>

      <div class="flex justify-end mt-2.5 mb-6">
        <button class="text-brand-600 text-sm hover:underline font-medium">Forgot password?</button>
      </div>

      <button class="btn-primary w-full btn-lg" :disabled="loading" @click="submit">
        <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        {{ loading ? "Signing in…" : "Sign In" }}
      </button>

      <div class="flex items-center gap-3 my-5">
        <div class="flex-1 h-px bg-slate-200"/>
        <span class="text-slate-400 text-xs">or</span>
        <div class="flex-1 h-px bg-slate-200"/>
      </div>

      <button class="btn-google" @click="googleLogin">
        <svg viewBox="0 0 48 48" class="w-5 h-5 shrink-0">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        </svg>
        Continue with Google
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { RouterLink, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import AuthPanel from "@/components/AuthPanel.vue"
import BaseInput from "@/components/BaseInput.vue"

const router = useRouter()
const auth   = useAuthStore()

const form     = reactive({ username: "", password: "" })
const errors   = reactive({ username: "", password: "" })
const loading  = ref(false)
const errorMsg = ref("")
const successMsg = ref("")

function validate() {
  errors.username = form.username ? "" : "Username is required."
  errors.password = form.password ? "" : "Password is required."
  return !errors.username && !errors.password
}

async function submit() {
  errorMsg.value = ""
  successMsg.value = ""
  if (!validate()) return
  loading.value = true
  try {
    await auth.login({ username: form.username, password: form.password })
    successMsg.value = "✓ Signed in! Redirecting…"
    setTimeout(() => router.replace("/home"), 900)
  } catch (err) {
    const d = err.response?.data
    errorMsg.value = d?.detail ?? d?.non_field_errors?.[0] ?? "Invalid credentials."
  } finally {
    loading.value = false
  }
}

function googleLogin() { alert("Google OAuth not configured yet.") }
</script>

<style scoped>
.alert-enter-active, .alert-leave-active { transition: all .25s ease; }
.alert-enter-from { opacity: 0; transform: translateY(-6px); }
.alert-leave-to   { opacity: 0; }
</style>
