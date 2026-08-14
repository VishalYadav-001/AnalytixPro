<template>
  <div class="hidden md:flex w-[360px] shrink-0 flex-col justify-between bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 p-10 text-white relative overflow-hidden">
    <!-- Background decoration -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-white/5 blur-3xl"/>
      <div class="absolute -bottom-10 -left-10 w-48 h-48 rounded-full bg-white/5 blur-2xl"/>
    </div>

    <!-- Logo -->
    <div class="flex items-center gap-3 relative z-10">
      <div class="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
        <svg viewBox="0 0 24 24" class="w-6 h-6 text-white" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <span class="font-display font-bold text-xl">AnalytixPro</span>
    </div>

    <!-- Features list -->
    <div class="space-y-5 relative z-10">
      <h2 class="font-display font-bold text-2xl leading-tight">
        Turn your data into<br/>actionable insights
      </h2>
      <div class="space-y-3">
        <Feature icon="upload" text="Upload CSV & Excel datasets instantly" />
        <Feature icon="bot"    text="AI chatbot guides your analysis flow" />
        <Feature icon="bar"    text="Auto-generate interactive dashboards" />
        <Feature icon="export" text="Export PDF, Jupyter & Python reports" />
      </div>
    </div>

    <!-- Testimonial -->
    <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-5 relative z-10">
      <p class="text-sm text-white/90 leading-relaxed">
        "AnalytixPro cut our reporting time by 80%. The AI-generated dashboards are production-ready instantly."
      </p>
      <p class="text-xs text-white/60 mt-3 font-medium">— Data Science Team Lead</p>
    </div>
  </div>
</template>

<script setup>
const Feature = {
  props: ["icon", "text"],
  template: `
    <div class="flex items-center gap-3">
      <div class="w-7 h-7 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
        <svg class="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline v-if="icon==='upload'" points="16 16 12 12 8 16"/><line v-if="icon==='upload'" x1="12" y1="12" x2="12" y2="21"/>
          <path v-if="icon==='upload'" d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
          <circle v-if="icon==='bot'" cx="12" cy="12" r="3"/>
          <path v-if="icon==='bot'" d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
          <line v-if="icon==='bar'" x1="18" y1="20" x2="18" y2="10"/><line v-if="icon==='bar'" x1="12" y1="20" x2="12" y2="4"/>
          <line v-if="icon==='bar'" x1="6" y1="20" x2="6" y2="14"/>
          <path v-if="icon==='export'" d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline v-if="icon==='export'" points="7 10 12 15 17 10"/><line v-if="icon==='export'" x1="12" y1="15" x2="12" y2="3"/>
        </svg>
      </div>
      <span class="text-sm text-white/85">{{ text }}</span>
    </div>
  `
}
</script>
