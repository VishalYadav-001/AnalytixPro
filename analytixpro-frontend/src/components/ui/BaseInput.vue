<template>
  <div>
    <label v-if="label" :for="id" class="label">{{ label }}</label>
    <div class="relative">
      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        class="input-base pr-10"
        :class="[error ? 'input-error' : '', $attrs.class]"
        v-bind="$attrs"
        @input="$emit('update:modelValue', $event.target.value)"
        @keydown.enter="$emit('enter')"
      />
      <!-- Password toggle -->
      <button
        v-if="type === 'password'"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
        @click="showPassword = !showPassword"
        tabindex="-1"
      >
        <svg v-if="showPassword" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
          <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
          <line x1="1" y1="1" x2="23" y2="23"/>
        </svg>
        <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
      </button>
    </div>
    <p v-if="error" class="mt-1 text-xs text-red-500">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-xs text-slate-400">{{ hint }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"

defineOptions({ inheritAttrs: false })

const props = defineProps({
  id:          String,
  modelValue:  { type: String, default: "" },
  label:       String,
  type:        { type: String, default: "text" },
  placeholder: String,
  error:       String,
  hint:        String,
  disabled:    Boolean,
})

defineEmits(["update:modelValue", "enter"])

const showPassword = ref(false)
const inputType = computed(() => {
  if (props.type === "password") return showPassword.value ? "text" : "password"
  return props.type || "text"
})
</script>
