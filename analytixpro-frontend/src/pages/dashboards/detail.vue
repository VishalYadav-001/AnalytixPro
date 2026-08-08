<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden" v-if="dashboard">

    <!-- ══ Main Dashboard Area ══════════════════════════════════════ -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">

      <!-- Sticky Header -->
      <header class="shrink-0 bg-white border-b border-slate-200 px-5 md:px-7 py-3 flex items-center justify-between gap-3 z-10">
        <div class="flex items-center gap-3 min-w-0">
          <button @click="$router.push('/dashboards')"
                  class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors shrink-0">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <div class="w-px h-5 bg-slate-200 hidden sm:block shrink-0"/>
          <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
               :style="{ background: domainColor + '15', color: domainColor }">
            <span v-html="domainSvg" class="w-4 h-4 block [&>svg]:w-4 [&>svg]:h-4"/>
          </div>
          <h1 class="font-semibold text-slate-900 text-sm truncate max-w-[160px] md:max-w-md">{{ dashboard.title }}</h1>
          <span class="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border hidden sm:inline"
                :style="{ background: domainColor + '10', color: domainColor, borderColor: domainColor + '25' }">
            {{ analysisTypeLabel }}
          </span>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <!-- Export dropdown -->
          <div class="relative" ref="exportDropRef">
            <button @click="exportOpen = !exportOpen" :disabled="!!exportLoading"
                    class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-medium transition-all disabled:opacity-50">
              <svg v-if="exportLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span class="hidden sm:inline">{{ exportLoading || 'Export' }}</span>
            </button>
            <Transition name="dd">
              <div v-if="exportOpen" class="absolute right-0 top-full mt-2 w-52 bg-white border border-slate-200 rounded-xl shadow-lg z-50 py-1.5 overflow-hidden">
                <button v-for="opt in EXPORT_OPTIONS" :key="opt.fmt" @click="doExport(opt.fmt)"
                        class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 transition-colors text-left">
                  <span v-html="opt.icon" class="w-4 h-4 text-slate-500 shrink-0 [&>svg]:w-4 [&>svg]:h-4"/>
                  <div>
                    <div class="text-xs font-semibold text-slate-800">{{ opt.label }}</div>
                    <div class="text-[10px] text-slate-400">{{ opt.desc }}</div>
                  </div>
                </button>
              </div>
            </Transition>
          </div>

          <!-- AI panel toggle -->
          <button @click="panelOpen = !panelOpen"
                  class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all border"
                  :class="panelOpen ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span class="hidden sm:inline">{{ panelOpen ? 'Close' : 'AI Edit' }}</span>
          </button>
        </div>
      </header>

      <!-- Alerts -->
      <div v-if="error || exportSuccess" class="shrink-0 px-5 md:px-7 pt-3">
        <div v-if="error" class="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-2.5 rounded-xl text-sm">
          <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {{ error }}
        </div>
        <div v-if="exportSuccess" class="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-2.5 rounded-xl text-sm">
          <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
          {{ exportSuccess }}
        </div>
      </div>

      <!-- Scrollable content -->
      <div class="flex-1 overflow-y-auto">
        <div class="max-w-screen-xl mx-auto px-5 md:px-7 py-6 space-y-8 pb-10">

          <!-- Meta row -->
          <div class="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
            <span class="flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v6c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 11v6c0 1.66 4 3 9 3s9-1.34 9-3v-6"/></svg>
              {{ dashboard.dataset_name }}
            </span>
            <span class="flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              {{ formatDate(dashboard.created_at) }}
            </span>
            <span v-if="targetColumn && targetColumn !== '__none__'" class="flex items-center gap-1.5 font-medium" :style="{ color: domainColor }">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
              Primary: {{ targetColumn }}
            </span>
          </div>

          <!-- ══ KPI Cards ══ -->
          <section v-if="kpiList.length && !isHidden('kpi')">
            <SectionLabel :title="sectionTitle('kpi')" />
            <div class="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              <div v-for="(kpi, i) in kpiList" :key="kpi.column"
                   class="bg-white rounded-2xl border p-5 transition-all duration-200 hover:shadow-md"
                   :class="isHighlighted(kpi.column) ? 'border-violet-200 shadow-sm shadow-violet-50' : 'border-slate-100 shadow-sm'">
                <!-- Icon + Label -->
                <div class="flex items-start justify-between mb-4">
                  <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                       :style="{ background: PALETTE[i % PALETTE.length] + '12', color: PALETTE[i % PALETTE.length] }">
                    <span v-html="KPI_SVG[i % KPI_SVG.length]" class="w-4 h-4 [&>svg]:w-4 [&>svg]:h-4 block"/>
                  </div>
                  <span class="text-[10px] font-semibold text-slate-400 truncate ml-2 mt-1 text-right leading-tight max-w-[65%]">{{ kpi.column }}</span>
                </div>
                <!-- Value -->
                <p class="text-[22px] font-bold tracking-tight leading-none tabular-nums"
                   :style="{ color: PALETTE[i % PALETTE.length] }">{{ fmt(kpi.mean) }}</p>
                <p class="text-[10px] text-slate-400 mt-0.5 mb-3">avg · σ {{ fmt(kpi.std) }}</p>
                <!-- Range bar -->
                <div class="h-1 bg-slate-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full"
                       :style="{ width: rangePercent(kpi) + '%', background: PALETTE[i % PALETTE.length] }"/>
                </div>
                <div class="flex justify-between text-[10px] tabular-nums text-slate-400 mt-1.5">
                  <span>{{ fmt(kpi.min) }}</span>
                  <span>{{ fmt(kpi.max) }}</span>
                </div>
              </div>
            </div>
          </section>

          <!-- ══ Overview: Numeric Bar + Category Bar (2-col) ══ -->
          <section v-if="(numColumns.length || catColumns.length) && !isHidden('overview')">
            <SectionLabel :title="sectionTitle('overview')" />
            <div class="mt-4 grid md:grid-cols-2 gap-5">
              <div v-if="numColumns.length" class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                <div class="flex items-center justify-between mb-1">
                  <p class="text-[11px] font-semibold text-slate-700 uppercase tracking-wider">{{ numColumns[0] }}</p>
                  <span class="text-[10px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-600 font-medium">Numeric</span>
                </div>
                <p class="text-[10px] text-slate-400 mb-4">Min · Mean · Median · Max · Std Dev</p>
                <div class="h-52 relative"><canvas ref="overviewBarEl"/></div>
              </div>
              <div v-if="catColumns.length" class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                <div class="flex items-center justify-between mb-1">
                  <p class="text-[11px] font-semibold text-slate-700 uppercase tracking-wider">{{ catColumns[0] }}</p>
                  <span class="text-[10px] px-2 py-0.5 rounded-md bg-violet-50 text-violet-600 font-medium">Category</span>
                </div>
                <p class="text-[10px] text-slate-400 mb-4">Top categories by frequency</p>
                <div class="h-52 relative"><canvas ref="overviewCatEl"/></div>
              </div>
            </div>
          </section>

          <!-- ══ Correlation Heatmap ══ -->
          <section v-if="!isHidden('correlation')">
            <SectionLabel :title="sectionTitle('correlation')" />
            <div class="mt-4 bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
              <div v-if="corrCols.length">
                <div class="overflow-x-auto">
                  <table class="border-collapse mx-auto text-[11px]">
                    <thead>
                      <tr>
                        <th class="p-2 w-24"/>
                        <th v-for="col in corrCols" :key="col"
                            class="p-2 text-center font-medium text-slate-500 text-[10px]">
                          <span class="block truncate max-w-[60px]" :title="col">{{ col.length > 8 ? col.slice(0,7)+'…' : col }}</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="row in corrCols" :key="row">
                        <td class="p-2 text-[10px] font-medium text-slate-500 text-right pr-3 truncate max-w-[90px]" :title="row">
                          {{ row.length > 9 ? row.slice(0,8)+'…' : row }}
                        </td>
                        <td v-for="col in corrCols" :key="col" class="p-1">
                          <div class="w-[52px] h-9 rounded-lg flex items-center justify-center font-mono text-[10px] font-semibold select-none cursor-default transition-transform hover:scale-105"
                               :style="corrStyle(analysis.correlation_matrix[row]?.[col])"
                               :title="`${row} × ${col}: ${formatCorr(analysis.correlation_matrix[row]?.[col])}`">
                            {{ formatCorr(analysis.correlation_matrix[row]?.[col]) }}
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <!-- Legend -->
                <div class="flex items-center justify-center gap-6 mt-5 text-[10px] text-slate-400">
                  <div class="flex items-center gap-1.5"><div class="w-8 h-2.5 rounded" style="background:rgba(220,38,38,0.55)"/><span>−1 negative</span></div>
                  <div class="flex items-center gap-1.5"><div class="w-8 h-2.5 rounded bg-slate-100"/><span>0 neutral</span></div>
                  <div class="flex items-center gap-1.5"><div class="w-8 h-2.5 rounded" style="background:rgba(37,99,235,0.55)"/><span>+1 positive</span></div>
                </div>
              </div>
              <div v-else class="h-32 flex items-center justify-center text-sm text-slate-400">No numeric columns for correlation analysis.</div>
            </div>
          </section>

          <!-- ══ Data Quality & Summary (2-col) ══ -->
          <section v-if="!isHidden('quality')">
            <SectionLabel title="Data Quality" />
            <div class="mt-4 grid md:grid-cols-2 gap-5">
              <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                <p class="text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-4">Missing Values</p>
                <div v-if="hasMissing" class="h-52 relative"><canvas ref="missingChartEl"/></div>
                <div v-else class="h-52 flex flex-col items-center justify-center gap-3 text-center">
                  <div class="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center">
                    <svg class="w-6 h-6 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                  <div>
                    <p class="font-semibold text-emerald-700 text-sm">No missing values</p>
                    <p class="text-[11px] text-slate-400 mt-0.5">Dataset is 100% complete</p>
                  </div>
                </div>
              </div>
              <div v-if="analysis?.summary_statistics" class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 overflow-hidden">
                <p class="text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-4">Summary Statistics</p>
                <div class="overflow-auto max-h-52">
                  <table class="w-full text-[11px]">
                    <thead class="sticky top-0 bg-white">
                      <tr class="border-b border-slate-100">
                        <th class="pb-2 text-left font-medium text-slate-500 text-[10px] uppercase tracking-wider">Column</th>
                        <th v-for="s in coreStatKeys" :key="s" class="pb-2 text-right font-medium text-slate-500 text-[10px] uppercase tracking-wider px-2">{{ s }}</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-50">
                      <tr v-for="(stats, col) in analysis.summary_statistics" :key="col"
                          class="hover:bg-slate-50/70 transition-colors">
                        <td class="py-2 font-mono text-[10px] font-medium text-slate-600 truncate max-w-[90px]" :title="col">{{ col }}</td>
                        <td v-for="s in coreStatKeys" :key="s" class="py-2 px-2 text-right font-mono text-[10px] text-slate-500 tabular-nums">{{ formatStat(stats[s]) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          <!-- ══ Categorical Distributions (3-col, horizontal bar) ══ -->
          <section v-if="catColumns.length && !isHidden('categorical')">
            <SectionLabel :title="sectionTitle('categorical')" />
            <div class="mt-4 grid md:grid-cols-2 lg:grid-cols-3 gap-5">
              <div v-for="col in catColumns" :key="col"
                   class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex flex-col"
                   :class="isHighlighted(col) ? 'border-violet-200 ring-1 ring-violet-100' : ''">
                <div class="flex items-center justify-between mb-1 shrink-0">
                  <p class="text-[11px] font-semibold text-slate-700 uppercase tracking-wider truncate max-w-[70%]">{{ col }}</p>
                  <span class="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-50 text-slate-500 shrink-0">{{ getCatEntries(col).length }} values</span>
                </div>
                <p class="text-[10px] text-slate-400 mb-3 shrink-0">Frequency breakdown</p>
                <div class="flex-1 min-h-0" style="height: 200px; position: relative;">
                  <canvas :ref="el => setCatRef(col, el)" style="width:100%;height:100%;"/>
                </div>
              </div>
            </div>
          </section>

          <!-- ══ Numeric Analysis (2-col) — advanced only ══ -->
          <section v-if="numColumns.length && !isHidden('numeric') && dashboard.level === 'advanced'">
            <SectionLabel :title="sectionTitle('numeric')" />
            <div class="mt-4 grid md:grid-cols-2 gap-5">
              <div v-for="col in numColumns" :key="col"
                   class="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex flex-col"
                   :class="isHighlighted(col) ? 'border-violet-200 ring-1 ring-violet-100' : ''">
                <div class="flex items-center justify-between mb-1 shrink-0">
                  <p class="text-[11px] font-semibold text-slate-700 uppercase tracking-wider truncate max-w-[65%]">{{ col }}</p>
                  <span class="text-[10px] tabular-nums text-slate-400 shrink-0">avg {{ fmt(analysis.top_kpis[col]?.mean) }}</span>
                </div>
                <p class="text-[10px] text-slate-400 mb-3 shrink-0">
                  σ {{ fmt(analysis.top_kpis[col]?.std) }} &nbsp;·&nbsp; {{ fmt(analysis.top_kpis[col]?.min) }} → {{ fmt(analysis.top_kpis[col]?.max) }}
                </p>
                <div class="flex-1 min-h-0" style="height: 180px; position: relative;">
                  <canvas :ref="el => setNumRef(col, el)" style="width:100%;height:100%;"/>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>

    <!-- ══ AI Command Panel ═══════════════════════════════════════════ -->
    <Transition name="panel">
      <aside v-if="panelOpen"
             class="w-[320px] shrink-0 flex flex-col bg-white border-l border-slate-200 h-full overflow-hidden">

        <!-- Panel header -->
        <div class="px-4 py-3.5 border-b border-slate-100 shrink-0 flex items-center justify-between bg-white">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-violet-600 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-1H1a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/></svg>
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-900 leading-none">AI Assistant</p>
              <p class="text-[10px] text-slate-400 mt-0.5">Edit dashboard with commands</p>
            </div>
          </div>
          <button @click="panelOpen = false"
                  class="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <!-- Messages -->
        <div ref="panelMessagesEl" class="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0">
          <div v-for="(msg, idx) in panelMessages" :key="idx"
               class="flex gap-2.5" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
            <div class="w-6 h-6 rounded-full shrink-0 flex items-center justify-center text-[9px] font-bold mt-0.5"
                 :class="msg.role === 'user' ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-500'">
              {{ msg.role === 'user' ? 'U' : 'AI' }}
            </div>
            <div class="max-w-[88%] px-3 py-2.5 rounded-xl text-[12px] leading-relaxed"
                 :class="msg.role === 'user'
                   ? 'bg-violet-600 text-white rounded-tr-none'
                   : 'bg-slate-100 text-slate-700 rounded-tl-none border border-slate-200/60'">
              <div v-html="renderMsg(msg.content)"/>
            </div>
          </div>
          <!-- Typing indicator -->
          <div v-if="cmdLoading" class="flex gap-2.5">
            <div class="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[9px] text-slate-500 shrink-0">AI</div>
            <div class="px-3 py-3 bg-slate-100 rounded-xl rounded-tl-none flex items-center gap-1">
              <span v-for="n in 3" :key="n" class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
                    :style="`animation-delay:${(n-1)*0.12}s`"/>
            </div>
          </div>
        </div>

        <!-- Quick command chips -->
        <div class="px-4 pb-2.5 shrink-0 flex flex-wrap gap-1.5 border-t border-slate-100 pt-3">
          <button v-for="chip in QUICK_COMMANDS" :key="chip"
                  @click="sendCommand(chip)" :disabled="cmdLoading"
                  class="px-2.5 py-1.5 text-[10px] font-medium rounded-lg bg-slate-50 border border-slate-200 text-slate-600 hover:bg-violet-50 hover:border-violet-200 hover:text-violet-700 transition-all disabled:opacity-40">
            {{ chip }}
          </button>
        </div>

        <!-- Input -->
        <div class="px-4 pb-4 shrink-0">
          <div class="relative">
            <input v-model="cmdInput"
                   @keydown.enter.prevent="sendCommand()"
                   :disabled="cmdLoading"
                   placeholder="Type a command..."
                   class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 pr-11 text-[13px] focus:outline-none focus:ring-2 focus:ring-violet-400/30 focus:bg-white transition-all disabled:opacity-60"/>
            <button @click="sendCommand()"
                    :disabled="!cmdInput.trim() || cmdLoading"
                    class="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 rounded-lg bg-violet-600 text-white flex items-center justify-center disabled:bg-slate-300 transition-all active:scale-95">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M22 2L11 13" stroke-width="2" stroke-linecap="round"/><path d="M22 2L15 22l-4-9-9-4 20-7z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </div>
      </aside>
    </Transition>

  </div>

  <!-- Loading skeleton -->
  <div v-else-if="loading" class="max-w-screen-xl mx-auto px-5 md:px-7 py-10 space-y-8">
    <div class="h-8 w-56 bg-slate-200 rounded-xl animate-pulse"/>
    <div class="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-5 gap-4">
      <div v-for="i in 5" :key="i" class="h-32 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
    <div class="grid md:grid-cols-2 gap-5">
      <div class="h-72 bg-slate-200 rounded-2xl animate-pulse"/>
      <div class="h-72 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
    <div class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
    <div class="grid md:grid-cols-2 gap-5">
      <div class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
      <div class="h-64 bg-slate-200 rounded-2xl animate-pulse"/>
    </div>
  </div>

  <div v-else class="flex items-center justify-center h-64 text-slate-400 text-sm">Dashboard not found.</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, defineComponent, h, watch } from "vue"
import { useRoute } from "vue-router"
import { dashboardService } from "@/services/api"
import {
  Chart, BarController, BarElement,
  CategoryScale, LinearScale,
  DoughnutController, ArcElement,
  Tooltip, Legend,
} from "chart.js"

Chart.register(BarController, BarElement, CategoryScale, LinearScale, DoughnutController, ArcElement, Tooltip, Legend)

// ── Inline SectionLabel ───────────────────────────────────────
const SectionLabel = defineComponent({
  props: ["title"],
  setup(p) {
    return () => h("div", { class: "flex items-center gap-3" }, [
      h("h2", { class: "text-[11px] font-bold text-slate-500 uppercase tracking-[0.12em] whitespace-nowrap" }, p.title),
      h("div", { class: "flex-1 h-px bg-slate-150" , style: "background:#e8ecf0" }),
    ])
  },
})

// ── Professional color palette ────────────────────────────────
const PALETTE = [
  "#2563eb","#7c3aed","#059669","#b45309","#dc2626",
  "#0891b2","#65a30d","#db2777","#c2410c","#0f766e",
]

// ── SVG icons for KPI cards ───────────────────────────────────
const KPI_SVG = [
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
]

// ── Domain SVG icons ──────────────────────────────────────────
const DOMAIN_SVG_MAP = {
  sales:     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  hr:        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  financial: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  custom:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
}

const EXPORT_OPTIONS = [
  { fmt: "pdf",   icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,   label: "PDF Report",       desc: "Formatted printable report" },
  { fmt: "ipynb", icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`, label: "Jupyter Notebook", desc: "Interactive Python notebook" },
  { fmt: "py",    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`, label: "Python Script",    desc: "Standalone runnable script"  },
]

const QUICK_COMMANDS = ["Simple view", "Full view", "Hide correlation", "Show all", "Reset", "Help"]
const DOMAIN_LABELS  = { sales: "Sales", hr: "HR Analytics", financial: "Finance", custom: "Analytics" }

// ── Base chart options (shared) ───────────────────────────────
const BASE_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 700, easing: "easeOutQuart" },
}

const TOOLTIP_DEFAULTS = {
  backgroundColor: "#1e293b",
  titleColor: "#e2e8f0",
  bodyColor: "#94a3b8",
  borderColor: "#334155",
  borderWidth: 1,
  padding: 10,
  cornerRadius: 8,
  displayColors: false,
}

// ── State ─────────────────────────────────────────────────────
const route         = useRoute()
const dashboard     = ref(null)
const analysis      = ref(null)
const loading       = ref(true)
const error         = ref("")
const exportLoading = ref("")
const exportSuccess = ref("")
const exportOpen    = ref(false)
const exportDropRef = ref(null)
const panelOpen     = ref(false)
const cmdInput      = ref("")
const cmdLoading    = ref(false)
const panelMessages = ref([])
const panelMessagesEl = ref(null)

const missingChartEl = ref(null)
const overviewBarEl  = ref(null)
const overviewCatEl  = ref(null)
const catRefs = {}
const numRefs = {}
const charts  = []

function setCatRef(col, el) { if (el) catRefs[col] = el }
function setNumRef(col, el) { if (el) numRefs[col] = el }

// ── Computed ──────────────────────────────────────────────────
const layoutConfig = computed(() => dashboard.value?.layout_config ?? {})
const commandState = computed(() => layoutConfig.value?.command_state ?? { hidden_sections: [], highlighted_columns: [], focus_type: null })
const analysisType = computed(() => layoutConfig.value?.analysis_type ?? "custom")
const domainColor  = computed(() => layoutConfig.value?.domain_color ?? "#2563eb")
const domainSvg    = computed(() => DOMAIN_SVG_MAP[analysisType.value] ?? DOMAIN_SVG_MAP.custom)
const analysisTypeLabel = computed(() => DOMAIN_LABELS[analysisType.value] ?? "Analytics")
const targetColumn = computed(() => layoutConfig.value?.target_column ?? "")

const kpiList = computed(() => {
  const k = analysis.value?.top_kpis
  if (!k) return []
  const all = Object.entries(k).map(([column, vals]) => ({ column, ...vals }))
  const tc = targetColumn.value
  if (tc && tc !== "__none__") {
    const idx = all.findIndex(k => k.column.toLowerCase() === tc.toLowerCase())
    if (idx > 0) { const [item] = all.splice(idx, 1); all.unshift(item) }
  }
  return all
})

const corrCols   = computed(() => Object.keys(analysis.value?.correlation_matrix ?? {}))
const catColumns = computed(() => Object.keys(analysis.value?.categorical_insights ?? {}))
const numColumns = computed(() => Object.keys(analysis.value?.top_kpis ?? {}))
const hasMissing = computed(() => {
  const m = analysis.value?.missing_values?.count
  return m && Object.values(m).some(v => v > 0)
})
const coreStatKeys = computed(() => {
  const s = analysis.value?.summary_statistics
  if (!s) return []
  const allKeys = Object.keys(Object.values(s)[0] || {})
  const preferred = ["count", "mean", "std", "min", "max"]
  const found = preferred.filter(k => allKeys.includes(k))
  return found.length ? found : allKeys.slice(0, 5)
})

function isHidden(section) { return (commandState.value?.hidden_sections ?? []).includes(section) }
function isHighlighted(col) {
  return (commandState.value?.highlighted_columns ?? []).some(h => h.toLowerCase() === col.toLowerCase())
}
function sectionTitle(key) {
  return layoutConfig.value?.sections?.[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
}

// ── Formatters ────────────────────────────────────────────────
function fmt(v) {
  if (v === null || v === undefined) return "—"
  const n = parseFloat(v)
  if (isNaN(n)) return String(v)
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
  if (Math.abs(n) >= 1_000)     return n.toLocaleString("en", { maximumFractionDigits: 1 })
  return n.toFixed(2)
}
function formatStat(v) {
  if (v === null || v === undefined || v === "") return "—"
  if (typeof v === "number") return Number.isInteger(v) ? v : v.toFixed(3)
  return String(v)
}
function formatCorr(v) {
  if (v === null || v === undefined) return "—"
  return parseFloat(v).toFixed(2)
}
function formatDate(v) {
  if (!v) return "—"
  return new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}
function corrStyle(v) {
  if (v === null || v === undefined) return { background: "#f8fafc", color: "#94a3b8" }
  const val = parseFloat(v), abs = Math.abs(val)
  if (abs < 0.05) return { background: "#f8fafc", color: "#94a3b8" }
  if (val > 0) return { background: `rgba(37,99,235,${0.1 + abs * 0.55})`, color: abs > 0.5 ? "#fff" : "#1d4ed8" }
  return { background: `rgba(220,38,38,${0.1 + abs * 0.55})`, color: abs > 0.5 ? "#fff" : "#b91c1c" }
}
function getCatEntries(col) {
  return Object.entries(analysis.value?.categorical_insights?.[col] || {}).slice(0, 8)
}
function rangePercent(kpi) {
  const range = (kpi.max ?? 0) - (kpi.min ?? 0)
  if (!range) return 50
  return Math.round(Math.max(4, Math.min(96, ((kpi.mean ?? 0) - (kpi.min ?? 0)) / range * 100)))
}
function renderMsg(content) {
  return (content || "")
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    .replace(/\n/g, "<br>")
}

// ── Gradient helper ───────────────────────────────────────────
function makeBarGradient(ctx, chartArea, hexColor) {
  const g = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
  g.addColorStop(0, hexColor + "ee")
  g.addColorStop(1, hexColor + "44")
  return g
}

// ── Chart builders ────────────────────────────────────────────
function destroyCharts() { charts.forEach(c => c.destroy()); charts.length = 0 }

function buildMissingChart() {
  const m = analysis.value?.missing_values?.count
  if (!m || !missingChartEl.value) return
  const entries = Object.entries(m).filter(([, v]) => v > 0)
  if (!entries.length) return
  const c = PALETTE[0]
  charts.push(new Chart(missingChartEl.value, {
    type: "bar",
    data: {
      labels: entries.map(([k]) => k.length > 12 ? k.slice(0, 11) + "…" : k),
      datasets: [{
        label: "Missing",
        data: entries.map(([, v]) => v),
        backgroundColor(ctx) {
          const chart = ctx.chart
          if (!chart.chartArea) return c + "cc"
          return makeBarGradient(chart.ctx, chart.chartArea, PALETTE[ctx.dataIndex % PALETTE.length])
        },
        borderWidth: 0,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      ...BASE_OPTS,
      plugins: { legend: { display: false }, tooltip: { ...TOOLTIP_DEFAULTS, callbacks: { label: ctx => ` ${ctx.parsed.y} missing` } } },
      scales: {
        x: { grid: { display: false }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
        y: { grid: { color: "#f1f5f9" }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } }, beginAtZero: true },
      },
    },
  }))
}

function buildOverviewBar() {
  if (!numColumns.value.length || !overviewBarEl.value) return
  const col = numColumns.value[0]
  const kpi = analysis.value?.top_kpis?.[col]
  if (!kpi) return
  const c = domainColor.value
  charts.push(new Chart(overviewBarEl.value, {
    type: "bar",
    data: {
      labels: ["Min", "Mean", "Median", "Max", "Std Dev"],
      datasets: [{
        label: col,
        data: [kpi.min, kpi.mean, kpi.median, kpi.max, kpi.std],
        backgroundColor(ctx) {
          const chart = ctx.chart
          if (!chart.chartArea) return c + "cc"
          return makeBarGradient(chart.ctx, chart.chartArea, c)
        },
        borderWidth: 0,
        borderRadius: { topLeft: 6, topRight: 6 },
        borderSkipped: false,
      }],
    },
    options: {
      ...BASE_OPTS,
      plugins: {
        legend: { display: false },
        tooltip: { ...TOOLTIP_DEFAULTS, callbacks: { label: ctx => ` ${fmt(ctx.parsed.y)}` } },
      },
      scales: {
        x: { grid: { display: false }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 11 } } },
        y: { grid: { color: "#f1f5f9" }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 11 } } },
      },
    },
  }))
}

function buildOverviewCat() {
  if (!catColumns.value.length || !overviewCatEl.value) return
  const entries = getCatEntries(catColumns.value[0])
  const c = PALETTE[1]
  charts.push(new Chart(overviewCatEl.value, {
    type: "bar",
    data: {
      labels: entries.map(([k]) => k.length > 14 ? k.slice(0, 12) + "…" : k),
      datasets: [{
        data: entries.map(([, v]) => v),
        backgroundColor(ctx) {
          const chart = ctx.chart
          if (!chart.chartArea) return c + "cc"
          return makeBarGradient(chart.ctx, chart.chartArea, PALETTE[ctx.dataIndex % PALETTE.length])
        },
        borderWidth: 0,
        borderRadius: { topLeft: 5, topRight: 5 },
        borderSkipped: false,
      }],
    },
    options: {
      ...BASE_OPTS,
      indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: { ...TOOLTIP_DEFAULTS, callbacks: { label: ctx => ` ${ctx.parsed.x.toLocaleString()}` } },
      },
      scales: {
        x: { grid: { color: "#f1f5f9" }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } }, beginAtZero: true },
        y: { grid: { display: false }, border: { display: false }, ticks: { color: "#475569", font: { size: 10, weight: "500" } } },
      },
    },
  }))
}

function buildCatCharts() {
  catColumns.value.forEach((col, ci) => {
    const el = catRefs[col]
    if (!el) return
    const entries = getCatEntries(col)
    const c = PALETTE[ci % PALETTE.length]
    charts.push(new Chart(el, {
      type: "bar",
      data: {
        labels: entries.map(([k]) => k.length > 16 ? k.slice(0, 14) + "…" : k),
        datasets: [{
          data: entries.map(([, v]) => v),
          backgroundColor(ctx) {
            const chart = ctx.chart
            if (!chart.chartArea) return c + "cc"
            return makeBarGradient(chart.ctx, chart.chartArea, c)
          },
          borderWidth: 0,
          borderRadius: { topLeft: 4, topRight: 4 },
          borderSkipped: false,
        }],
      },
      options: {
        ...BASE_OPTS,
        indexAxis: "y",
        plugins: {
          legend: { display: false },
          tooltip: { ...TOOLTIP_DEFAULTS, callbacks: { label: ctx => ` ${ctx.parsed.x.toLocaleString()} occurrences` } },
        },
        scales: {
          x: { grid: { color: "#f4f6f8" }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } }, beginAtZero: true },
          y: { grid: { display: false }, border: { display: false }, ticks: { color: "#475569", font: { size: 10, weight: "500" }, maxTicksLimit: 8 } },
        },
      },
    }))
  })
}

function buildNumCharts() {
  const kpis = analysis.value?.top_kpis
  if (!kpis) return
  numColumns.value.forEach((col, i) => {
    const el = numRefs[col]
    if (!el) return
    const s = kpis[col]
    if (!s) return
    const c = PALETTE[i % PALETTE.length]
    charts.push(new Chart(el, {
      type: "bar",
      data: {
        labels: ["Min", "Mean", "Median", "Max", "Std"],
        datasets: [{
          label: col,
          data: [s.min, s.mean, s.median, s.max, s.std],
          backgroundColor(ctx) {
            const chart = ctx.chart
            if (!chart.chartArea) return c + "cc"
            return makeBarGradient(chart.ctx, chart.chartArea, c)
          },
          borderWidth: 0,
          borderRadius: { topLeft: 5, topRight: 5 },
          borderSkipped: false,
        }],
      },
      options: {
        ...BASE_OPTS,
        plugins: {
          legend: { display: false },
          tooltip: { ...TOOLTIP_DEFAULTS, callbacks: { label: ctx => ` ${fmt(ctx.parsed.y)}` } },
        },
        scales: {
          x: { grid: { display: false }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
          y: { grid: { color: "#f4f6f8" }, border: { display: false }, ticks: { color: "#94a3b8", font: { size: 10 } } },
        },
      },
    }))
  })
}

async function buildAllCharts() {
  await nextTick()
  destroyCharts()
  buildMissingChart()
  buildOverviewBar()
  buildOverviewCat()
  buildCatCharts()
  buildNumCharts()
}

// ── Load ──────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const res = await dashboardService.get(route.params.id)
    dashboard.value = res.data
    analysis.value  = res.data.analysis ?? null
    await buildAllCharts()
  } catch {
    error.value = "Failed to load dashboard."
  } finally {
    loading.value = false
  }
}

// ── Command panel ─────────────────────────────────────────────
function initPanelMessages() {
  if (panelMessages.value.length) return
  panelMessages.value = [{
    role: "assistant",
    content: `Hi! I can update your **${analysisTypeLabel.value}** dashboard instantly.\n\nCommands:\n• **hide correlation**\n• **focus on Revenue**\n• **simple view** / **full view**\n• **show all** / **reset**\n• **help**`,
  }]
}

async function sendCommand(text) {
  const cmd = (text ?? cmdInput.value).trim()
  if (!cmd || cmdLoading.value) return
  cmdInput.value = ""
  panelMessages.value.push({ role: "user", content: cmd })
  await scrollPanel()
  cmdLoading.value = true
  try {
    const res = await dashboardService.command(route.params.id, cmd)
    panelMessages.value.push({ role: "assistant", content: res.data.message })
    if (res.data.layout_config) {
      dashboard.value = { ...dashboard.value, layout_config: res.data.layout_config }
      await buildAllCharts()
    }
  } catch {
    panelMessages.value.push({ role: "assistant", content: "Command failed. Please try again." })
  } finally {
    cmdLoading.value = false
    await scrollPanel()
  }
}

async function scrollPanel() {
  await nextTick()
  if (panelMessagesEl.value) panelMessagesEl.value.scrollTop = panelMessagesEl.value.scrollHeight
}

// ── Export ────────────────────────────────────────────────────
async function doExport(format) {
  exportOpen.value = false; error.value = ""; exportSuccess.value = ""
  exportLoading.value = format.toUpperCase()
  try {
    const res = await dashboardService.export(route.params.id, format)
    const url = res.data.file_url
    if (url) { window.open(url, "_blank"); exportSuccess.value = `${format.toUpperCase()} export ready!` }
    else exportSuccess.value = "Export queued successfully."
  } catch (err) {
    error.value = err.response?.data?.detail ?? "Export failed."
  } finally { exportLoading.value = "" }
}

function onOutsideClick(e) {
  if (exportDropRef.value && !exportDropRef.value.contains(e.target)) exportOpen.value = false
}

watch(panelOpen, val => { if (val) nextTick(initPanelMessages) })

onMounted(() => { load(); document.addEventListener("click", onOutsideClick) })
onUnmounted(() => { destroyCharts(); document.removeEventListener("click", onOutsideClick) })
</script>

<style scoped>
.panel-enter-active, .panel-leave-active { transition: width 0.22s ease, opacity 0.22s ease; overflow: hidden; }
.panel-enter-from, .panel-leave-to       { width: 0 !important; opacity: 0; }
.dd-enter-active, .dd-leave-active       { transition: all .15s ease; }
.dd-enter-from, .dd-leave-to             { opacity: 0; transform: translateY(-5px); }
</style>
