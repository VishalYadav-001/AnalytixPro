<template>
  <div class="w-full max-w-4xl bg-white rounded-3xl shadow-2xl overflow-hidden flex min-h-[640px] animate-fade-up">

    <AuthPanel />

    <div class="flex-1 flex flex-col justify-center px-8 py-10 md:px-12 overflow-y-auto">

      <!-- Tab switcher -->
      <div class="flex bg-slate-100 rounded-xl p-1 mb-8">
        <RouterLink to="/auth/login" class="tab-pill tab-pill-inactive">Sign In</RouterLink>
        <button class="tab-pill tab-pill-active ml-1" disabled>Create Account</button>
      </div>

      <div class="mb-7">
        <h1 class="font-display text-2xl font-bold text-slate-900">Create an account</h1>
        <p class="text-brand-600 text-sm mt-1">Start analysing your data with AI in minutes.</p>
      </div>

      <!-- Alerts -->
      <Transition name="alert">
        <div v-if="errorMsg" class="alert-error mb-5 flex items-start gap-2">
          <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4 mt-0.5 shrink-0" stroke="currentColor" stroke-width="2">
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
        <div class="grid grid-cols-2 gap-3">
          <BaseInput
            id="first-name"
            v-model="form.first_name"
            label="First Name"
            placeholder="Jane"
            :error="errors.first_name"
          />
          <BaseInput
            id="last-name"
            v-model="form.last_name"
            label="Last Name"
            placeholder="Doe"
            :error="errors.last_name"
          />
        </div>
        <BaseInput
          id="reg-username"
          v-model="form.username"
          label="Username"
          placeholder="jane_doe"
          :error="errors.username"
        />
        <BaseInput
          id="reg-email"
          v-model="form.email"
          label="Email"
          type="email"
          placeholder="jane@company.com"
          :error="errors.email"
        />
        <BaseInput
          id="reg-password"
          v-model="form.password"
          label="Password"
          type="password"
          placeholder="Min. 8 characters"
          :error="errors.password"
          hint="Must be at least 8 characters."
        />
        <BaseInput
          id="reg-password2"
          v-model="form.password2"
          label="Confirm Password"
          type="password"
          placeholder="Repeat your password"
          :error="errors.password2"
          @enter="submit"
        />
      </div>

      <button class="btn-primary w-full btn-lg mt-6" :disabled="loading" @click="submit">
        <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        {{ loading ? "Creating account…" : "Create Account" }}
      </button>

      <p class="text-center text-xs text-slate-400 mt-4">
        By signing up you agree to our
        <span class="text-brand-600 hover:underline cursor-pointer">Terms of Service</span>
        and <span class="text-brand-600 hover:underline cursor-pointer">Privacy Policy</span>.
      </p>
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

const form = reactive({
  first_name: "", last_name: "", username: "",
  email: "", password: "", password2: "",
})
const errors = reactive({
  first_name: "", last_name: "", username: "",
  email: "", password: "", password2: "",
})
const loading    = ref(false)
const errorMsg   = ref("")
const successMsg = ref("")

function validate() {
  let ok = true
  ;["first_name","last_name","username","email","password","password2"].forEach(k => errors[k] = "")
  if (!form.first_name) { errors.first_name = "Required."; ok = false }
  if (!form.last_name)  { errors.last_name  = "Required."; ok = false }
  if (!form.username)   { errors.username   = "Required."; ok = false }
  if (!form.email || !form.email.includes("@")) { errors.email = "Valid email required."; ok = false }
  if (form.password.length < 8) { errors.password = "Min. 8 characters."; ok = false }
  if (form.password !== form.password2) { errors.password2 = "Passwords do not match."; ok = false }
  return ok
}

async function submit() {
  errorMsg.value = ""
  successMsg.value = ""
  if (!validate()) return
  loading.value = true
  try {
    await auth.register({ ...form })
    successMsg.value = "✓ Account created! Redirecting…"
    setTimeout(() => router.replace("/home"), 1000)
  } catch (err) {
    const d = err.response?.data
    if (d && typeof d === "object") {
      Object.keys(d).forEach(k => { if (errors[k] !== undefined) errors[k] = d[k]?.[0] || d[k] })
      errorMsg.value = "Please fix the errors below."
    } else {
      errorMsg.value = "Registration failed. Please try again."
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.alert-enter-active, .alert-leave-active { transition: all .25s ease; }
.alert-enter-from { opacity: 0; transform: translateY(-6px); }
.alert-leave-to   { opacity: 0; }
</style>
