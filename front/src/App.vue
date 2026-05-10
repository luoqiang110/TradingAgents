<template>
  <main class="app-shell">
    <header class="topbar">
      <div class="brand-block">
        <p class="eyebrow">{{ t("brand.eyebrow") }}</p>
        <h1>{{ t("brand.title") }}</h1>
        <p class="subtitle">{{ t("brand.subtitle") }}</p>
      </div>

      <nav class="view-tabs" :aria-label="t('nav.primary')">
        <button
          type="button"
          :class="{ active: activeView === 'console' }"
          @click="activeView = 'console'"
        >
          <LayoutDashboard :size="17" />
          {{ t("nav.console") }}
        </button>
        <button
          type="button"
          :class="{ active: activeView === 'stats' }"
          @click="activeView = 'stats'"
        >
          <BarChart3 :size="17" />
          {{ t("nav.statistics") }}
        </button>
      </nav>

      <div class="topbar-actions">
        <div class="locale-switch" :aria-label="t('language.switch')">
          <button
            type="button"
            :class="{ active: activeLocale === 'zh-CN' }"
            @click="setLocale('zh-CN')"
          >
            中文
          </button>
          <button
            type="button"
            :class="{ active: activeLocale === 'en-US' }"
            @click="setLocale('en-US')"
          >
            EN
          </button>
        </div>
        <div class="health" :class="healthState">
          <Server :size="16" />
          <span>{{ healthLabel }}</span>
        </div>
        <label class="api-key">
          <ShieldCheck :size="16" />
          <input
            v-model="apiKey"
            type="password"
            placeholder="API Key"
            autocomplete="off"
            @change="persistApiKey"
          />
        </label>
      </div>
    </header>

    <section class="summary-strip">
      <article class="summary-card">
        <span class="summary-icon blue"><Layers :size="18" /></span>
        <div>
          <strong>{{ stats.total }}</strong>
          <small>{{ t("summary.total") }}</small>
        </div>
      </article>
      <article class="summary-card">
        <span class="summary-icon green"><CheckCircle2 :size="18" /></span>
        <div>
          <strong>{{ stats.completed }}</strong>
          <small>{{ t("summary.completed") }}</small>
        </div>
      </article>
      <article class="summary-card">
        <span class="summary-icon amber"><Loader2 :size="18" /></span>
        <div>
          <strong>{{ stats.active }}</strong>
          <small>{{ t("summary.active") }}</small>
        </div>
      </article>
      <article class="summary-card">
        <span class="summary-icon red"><AlertTriangle :size="18" /></span>
        <div>
          <strong>{{ stats.failed }}</strong>
          <small>{{ t("summary.failed") }}</small>
        </div>
      </article>
    </section>

    <section v-if="activeView === 'console'" class="workspace">
      <form class="panel form-panel" @submit.prevent="submitAnalysis">
        <div class="panel-title">
          <Settings :size="18" />
          <h2>{{ t("analysis.title") }}</h2>
        </div>

        <div class="form-grid">
          <label class="ticker-field">
            <span>{{ t("form.ticker") }}</span>
            <input
              v-model.trim="form.ticker"
              required
              maxlength="32"
              placeholder="NVDA / 300502.SZ / ZTKJ"
              autocomplete="off"
              role="combobox"
              :aria-expanded="tickerSearchOpen && tickerSuggestions.length > 0"
              aria-controls="ticker-suggestions"
              @focus="openTickerSearch"
              @input="openTickerSearch"
              @keydown.down.prevent="moveTickerHighlight(1)"
              @keydown.up.prevent="moveTickerHighlight(-1)"
              @keydown.enter="handleTickerEnter"
              @keydown.esc="tickerSearchOpen = false"
              @blur="closeTickerSearchSoon"
            />
            <div v-if="selectedTickerPreview" class="ticker-selected">
              <strong>{{ selectedTickerPreview.symbol }}</strong>
              <span>{{ selectedTickerPreview.name }}</span>
            </div>
            <div
              v-if="tickerSearchOpen && tickerSuggestions.length > 0"
              id="ticker-suggestions"
              class="ticker-suggestions"
              role="listbox"
            >
              <button
                v-for="(item, index) in tickerSuggestions"
                :key="`${item.symbol}-${item.name}`"
                type="button"
                class="ticker-suggestion"
                :class="{ active: highlightedTickerSuggestion === index }"
                role="option"
                :aria-selected="highlightedTickerSuggestion === index"
                @mousedown.prevent="selectTickerSuggestion(item)"
                @mouseenter="highlightedTickerSuggestion = index"
              >
                <span>
                  <strong>{{ item.symbol }}</strong>
                  <small>{{ item.name }}</small>
                </span>
                <em>{{ item.initials }}</em>
              </button>
            </div>
            <small class="field-hint">{{ t("form.tickerHint") }}</small>
          </label>
          <label>
            <span>{{ t("form.tradeDate") }}</span>
            <input v-model="form.trade_date" required type="date" />
          </label>
          <label>
            <span>{{ t("form.provider") }}</span>
            <select v-model="form.llm_provider">
              <option v-for="provider in options.providers" :key="provider" :value="provider">
                {{ provider }}
              </option>
            </select>
          </label>
          <label>
            <span>{{ t("form.outputLanguage") }}</span>
            <select v-model="form.output_language">
              <option v-for="language in options.languages" :key="language" :value="language">
                {{ language }}
              </option>
            </select>
          </label>
          <label>
            <span>{{ t("form.quickModel") }}</span>
            <input v-model.trim="form.quick_think_llm" placeholder="deepseek-chat" />
          </label>
          <label>
            <span>{{ t("form.deepModel") }}</span>
            <input v-model.trim="form.deep_think_llm" placeholder="deepseek-reasoner" />
          </label>
        </div>

        <div class="control-row">
          <span>{{ t("form.researchDepth") }}</span>
          <div class="segmented">
            <button
              v-for="depth in [1, 3, 5]"
              :key="depth"
              type="button"
              :class="{ active: form.research_depth === depth }"
              @click="form.research_depth = depth"
            >
              {{ depth }}
            </button>
          </div>
        </div>

        <div class="analyst-grid">
          <label v-for="analyst in options.analysts" :key="analyst" class="check-tile">
            <input v-model="form.analysts" type="checkbox" :value="analyst" />
            <span>{{ analystLabels[analyst] || analyst }}</span>
          </label>
        </div>

        <label class="switch-row">
          <input v-model="form.checkpoint_enabled" type="checkbox" />
          <span>{{ t("form.checkpoint") }}</span>
        </label>

        <p v-if="error" class="message error">
          <AlertTriangle :size="16" />
          {{ error }}
        </p>
        <p v-if="notice" class="message success">
          <CheckCircle2 :size="16" />
          {{ notice }}
        </p>

        <button class="primary-action" type="submit" :disabled="submitting || form.analysts.length === 0">
          <Loader2 v-if="submitting" class="spin" :size="18" />
          <Play v-else :size="18" />
          <span>{{ submitting ? t("action.submitting") : t("action.start") }}</span>
        </button>
      </form>

      <aside class="panel jobs-panel">
        <div class="panel-title">
          <Activity :size="18" />
          <h2>{{ t("jobs.title") }}</h2>
          <button class="icon-button" type="button" :title="t('action.refresh')" @click="refreshJobs">
            <RefreshCw :size="16" />
          </button>
        </div>

        <div class="jobs-list">
          <button
            v-for="job in jobs"
            :key="job.id"
            class="job-item"
            :class="{ selected: currentJob?.id === job.id }"
            type="button"
            @click="selectJob(job.id)"
          >
            <span class="job-main">
              <strong>{{ job.request.ticker }}</strong>
              <small>{{ formatTickerSubtitle(job.request.ticker, job.request.trade_date) }}</small>
            </span>
            <span class="status-pill" :class="job.status">
              <Clock v-if="job.status === 'queued'" :size="14" />
              <Loader2 v-else-if="job.status === 'running'" class="spin" :size="14" />
              <CheckCircle2 v-else-if="job.status === 'completed'" :size="14" />
              <AlertTriangle v-else :size="14" />
              {{ statusLabels[job.status] || job.status }}
            </span>
          </button>
          <p v-if="jobs.length === 0" class="empty">{{ t("jobs.empty") }}</p>
        </div>
      </aside>

      <section class="panel report-panel">
        <div class="panel-title">
          <FileText :size="18" />
          <h2>{{ t("report.title") }}</h2>
          <button
            v-if="currentJob"
            class="icon-button danger"
            type="button"
            :title="t('action.delete')"
            @click="deleteCurrentJob"
          >
            <Trash2 :size="16" />
          </button>
        </div>

        <div v-if="currentJob" class="report-meta">
          <span>{{ currentJob.request.ticker }}</span>
          <span>{{ currentJob.request.trade_date }}</span>
          <span class="status-pill" :class="currentJob.status">
            {{ statusLabels[currentJob.status] || currentJob.status }}
          </span>
        </div>

        <p v-if="currentJob?.error" class="message error">
          <AlertTriangle :size="16" />
          {{ currentJob.error }}
        </p>

        <div v-if="reportTabs.length > 0" class="tabs">
          <button
            v-for="tab in reportTabs"
            :key="tab.key"
            type="button"
            :class="{ active: activeReportKey === tab.key }"
            @click="activeReportKey = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <article v-if="activeReport" class="report-content">
          <pre>{{ activeReport }}</pre>
        </article>
        <div v-else class="empty-report">
          <FileText :size="28" />
          <p>{{ currentJob ? t("report.pending") : t("report.empty") }}</p>
        </div>
      </section>
    </section>

    <section v-else class="stats-dashboard">
      <article class="panel metric-card">
        <div class="metric-head">
          <span class="summary-icon blue"><BarChart3 :size="18" /></span>
          <small>{{ t("stats.completionRate") }}</small>
        </div>
        <strong>{{ stats.completionRate }}%</strong>
        <p>{{ t("stats.completedOf", { completed: stats.completed, total: stats.total }) }}</p>
      </article>

      <article class="panel metric-card">
        <div class="metric-head">
          <span class="summary-icon green"><Timer :size="18" /></span>
          <small>{{ t("stats.averageDuration") }}</small>
        </div>
        <strong>{{ stats.averageDuration }}</strong>
        <p>{{ t("stats.durationHint") }}</p>
      </article>

      <article class="panel metric-card">
        <div class="metric-head">
          <span class="summary-icon amber"><Briefcase :size="18" /></span>
          <small>{{ t("stats.topProvider") }}</small>
        </div>
        <strong>{{ topProvider.label }}</strong>
        <p>{{ t("stats.jobCount", { count: topProvider.count }) }}</p>
      </article>

      <article class="panel metric-card">
        <div class="metric-head">
          <span class="summary-icon red"><TrendingUp :size="18" /></span>
          <small>{{ t("stats.topTicker") }}</small>
        </div>
        <strong>{{ topTicker.label }}</strong>
        <p>{{ t("stats.jobCount", { count: topTicker.count }) }}</p>
      </article>

      <article class="panel stats-panel wide">
        <div class="panel-title">
          <PieChart :size="18" />
          <h2>{{ t("stats.statusMix") }}</h2>
        </div>
        <div class="status-meter" :aria-label="t('stats.statusDistribution')">
          <span
            v-for="segment in statusSegments"
            :key="segment.key"
            :class="segment.key"
            :style="{ width: `${segment.percent}%` }"
          />
        </div>
        <div class="status-grid">
          <div v-for="segment in statusSegments" :key="segment.key" class="status-row">
            <span class="dot" :class="segment.key"></span>
            <span>{{ segment.label }}</span>
            <strong>{{ segment.count }}</strong>
            <small>{{ segment.percent }}%</small>
          </div>
        </div>
      </article>

      <article class="panel stats-panel">
        <div class="panel-title">
          <Layers :size="18" />
          <h2>{{ t("stats.analystCoverage") }}</h2>
        </div>
        <div class="bar-list">
          <div v-for="item in analystUsage" :key="item.key" class="bar-row">
            <div class="bar-meta">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
            <div class="bar-track">
              <span :style="{ width: `${item.percent}%` }"></span>
            </div>
          </div>
        </div>
      </article>

      <article class="panel stats-panel">
        <div class="panel-title">
          <Briefcase :size="18" />
          <h2>{{ t("stats.providerMix") }}</h2>
        </div>
        <div class="bar-list">
          <div v-for="item in providerUsage" :key="item.key" class="bar-row">
            <div class="bar-meta">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
            <div class="bar-track provider">
              <span :style="{ width: `${item.percent}%` }"></span>
            </div>
          </div>
        </div>
      </article>

      <article class="panel stats-panel wide">
        <div class="panel-title">
          <CalendarDays :size="18" />
          <h2>{{ t("stats.recentActivity") }}</h2>
          <button class="icon-button" type="button" :title="t('action.refresh')" @click="refreshJobs">
            <RefreshCw :size="16" />
          </button>
        </div>
        <div class="activity-table">
          <div class="activity-head">
            <span>{{ t("table.ticker") }}</span>
            <span>{{ t("table.name") }}</span>
            <span>{{ t("table.status") }}</span>
            <span>{{ t("table.provider") }}</span>
            <span>{{ t("table.duration") }}</span>
          </div>
          <div v-for="job in recentJobs" :key="job.id" class="activity-row">
            <strong>{{ job.request.ticker }}</strong>
            <span>{{ tickerDisplayName(job.request.ticker) || "-" }}</span>
            <span class="status-pill" :class="job.status">{{ statusLabels[job.status] || job.status }}</span>
            <span>{{ job.request.llm_provider || options.defaults.llm_provider || t("common.default") }}</span>
            <span>{{ formatDuration(durationMs(job)) }}</span>
          </div>
          <p v-if="recentJobs.length === 0" class="empty">{{ t("stats.empty") }}</p>
        </div>
      </article>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { pinyin } from "pinyin-pro";
import aShareSearchData from "./data/a_share_search.json";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Briefcase,
  CalendarDays,
  CheckCircle2,
  Clock,
  FileText,
  Layers,
  LayoutDashboard,
  Loader2,
  PieChart,
  Play,
  RefreshCw,
  Server,
  Settings,
  ShieldCheck,
  Timer,
  Trash2,
  TrendingUp
} from "lucide-vue-next";
import { apiRequest, getHealth, getStoredApiKey, setStoredApiKey } from "./api";

const LOCALE_STORAGE = "tradingagents_ui_locale";

const messages = {
  "zh-CN": {
    "brand.eyebrow": "TradingAgents 控制台",
    "brand.title": "投研分析工作台",
    "brand.subtitle": "启动多智能体投研任务，跟踪运行进度，并查看运营统计。",
    "nav.primary": "主视图",
    "nav.console": "控制台",
    "nav.statistics": "统计",
    "language.switch": "切换界面语言",
    "health.checking": "检查中",
    "health.ok": "后端在线",
    "health.down": "后端离线",
    "summary.total": "总任务",
    "summary.completed": "已完成",
    "summary.active": "运行中",
    "summary.failed": "失败",
    "analysis.title": "新建分析",
    "form.ticker": "股票代码",
    "form.tickerHint": "请输入交易所代码，例如 300502.SZ；A 股也支持中文简称，例如 贵州茅台、新易盛。",
    "form.tradeDate": "交易日期",
    "form.provider": "LLM 服务商",
    "form.outputLanguage": "报告语言",
    "form.quickModel": "快速模型",
    "form.deepModel": "深度模型",
    "form.researchDepth": "研究深度",
    "form.checkpoint": "启用 checkpoint 续跑",
    "action.start": "启动分析",
    "action.submitting": "提交中",
    "action.refresh": "刷新任务",
    "action.delete": "删除当前任务",
    "jobs.title": "任务",
    "jobs.empty": "暂无任务",
    "report.title": "报告",
    "report.pending": "报告会在任务完成后显示",
    "report.empty": "请选择或创建一个分析任务",
    "stats.completionRate": "完成率",
    "stats.completedOf": "{completed} / {total} 个任务已完成",
    "stats.averageDuration": "平均耗时",
    "stats.durationHint": "基于带运行时间的已完成任务",
    "stats.topProvider": "最常用服务商",
    "stats.topTicker": "最常分析标的",
    "stats.jobCount": "{count} 个任务",
    "stats.statusMix": "状态分布",
    "stats.statusDistribution": "任务状态分布",
    "stats.analystCoverage": "分析师覆盖",
    "stats.providerMix": "服务商分布",
    "stats.recentActivity": "最近活动",
    "stats.empty": "暂无可统计任务",
    "table.ticker": "标的",
    "table.name": "名称",
    "table.status": "状态",
    "table.provider": "服务商",
    "table.duration": "耗时",
    "status.queued": "排队",
    "status.running": "运行中",
    "status.completed": "完成",
    "status.failed": "失败",
    "analyst.market": "市场",
    "analyst.social": "社媒",
    "analyst.news": "新闻",
    "analyst.fundamentals": "基本面",
    "report.market": "市场",
    "report.sentiment": "情绪",
    "report.news": "新闻",
    "report.fundamentals": "基本面",
    "report.research": "研究",
    "report.trader": "交易员",
    "report.decision": "决策",
    "common.none": "暂无",
    "common.default": "默认",
    "duration.zero": "0 秒",
    "duration.seconds": "{seconds} 秒",
    "duration.minutes": "{minutes} 分 {seconds} 秒",
    "notice.apiKeySaved": "API Key 已保存到当前浏览器",
    "notice.jobSubmitted": "任务已提交",
    "error.invalidTicker": "请输入交易所股票代码，例如 NVDA、SPY、300502.SZ、0700.HK；A 股可直接输入中文简称。"
  },
  "en-US": {
    "brand.eyebrow": "TradingAgents Console",
    "brand.title": "Research Dashboard",
    "brand.subtitle": "Launch multi-agent analysis, track progress, and review operating stats.",
    "nav.primary": "Primary views",
    "nav.console": "Console",
    "nav.statistics": "Statistics",
    "language.switch": "Switch interface language",
    "health.checking": "Checking",
    "health.ok": "Backend online",
    "health.down": "Backend offline",
    "summary.total": "Total jobs",
    "summary.completed": "Completed",
    "summary.active": "Active",
    "summary.failed": "Failed",
    "analysis.title": "New Analysis",
    "form.ticker": "Ticker Symbol",
    "form.tickerHint": "Use an exchange ticker such as 300502.SZ; A-share Chinese short names such as 贵州茅台 or 新易盛 are supported.",
    "form.tradeDate": "Trade Date",
    "form.provider": "LLM Provider",
    "form.outputLanguage": "Output Language",
    "form.quickModel": "Quick Model",
    "form.deepModel": "Deep Model",
    "form.researchDepth": "Research Depth",
    "form.checkpoint": "Enable checkpoint resume",
    "action.start": "Start Analysis",
    "action.submitting": "Submitting",
    "action.refresh": "Refresh jobs",
    "action.delete": "Delete current job",
    "jobs.title": "Jobs",
    "jobs.empty": "No jobs yet",
    "report.title": "Report",
    "report.pending": "The report will appear after completion",
    "report.empty": "Select or create an analysis job",
    "stats.completionRate": "Completion rate",
    "stats.completedOf": "{completed} of {total} jobs completed",
    "stats.averageDuration": "Average duration",
    "stats.durationHint": "Completed jobs with runtime data",
    "stats.topProvider": "Top provider",
    "stats.topTicker": "Most used ticker",
    "stats.jobCount": "{count} jobs",
    "stats.statusMix": "Status Mix",
    "stats.statusDistribution": "Job status distribution",
    "stats.analystCoverage": "Analyst Coverage",
    "stats.providerMix": "Provider Mix",
    "stats.recentActivity": "Recent Activity",
    "stats.empty": "No jobs to summarize yet",
    "table.ticker": "Ticker",
    "table.name": "Name",
    "table.status": "Status",
    "table.provider": "Provider",
    "table.duration": "Duration",
    "status.queued": "Queued",
    "status.running": "Running",
    "status.completed": "Done",
    "status.failed": "Failed",
    "analyst.market": "Market",
    "analyst.social": "Social",
    "analyst.news": "News",
    "analyst.fundamentals": "Fundamentals",
    "report.market": "Market",
    "report.sentiment": "Sentiment",
    "report.news": "News",
    "report.fundamentals": "Fundamentals",
    "report.research": "Research",
    "report.trader": "Trader",
    "report.decision": "Decision",
    "common.none": "None",
    "common.default": "default",
    "duration.zero": "0s",
    "duration.seconds": "{seconds}s",
    "duration.minutes": "{minutes}m {seconds}s",
    "notice.apiKeySaved": "API key saved in this browser",
    "notice.jobSubmitted": "Job submitted",
    "error.invalidTicker": "Use an exchange ticker symbol, for example NVDA, SPY, 300502.SZ, 0700.HK. A-share Chinese short names are supported."
  }
};

const today = new Date().toISOString().slice(0, 10);
const activeView = ref("console");
const activeLocale = ref(localStorage.getItem(LOCALE_STORAGE) || "zh-CN");
const apiKey = ref(getStoredApiKey());
const healthState = ref("checking");
const submitting = ref(false);
const error = ref("");
const notice = ref("");
const jobs = ref([]);
const currentJob = ref(null);
const activeReportKey = ref("");
const tickerSearchOpen = ref(false);
const highlightedTickerSuggestion = ref(0);
let pollTimer = null;

const options = reactive({
  analysts: ["market", "social", "news", "fundamentals"],
  providers: ["openai", "google", "anthropic", "deepseek", "qwen", "glm", "ollama"],
  languages: ["Chinese", "English"],
  ticker_aliases: {
    "新易盛": "300502.SZ",
    "300502": "300502.SZ"
  },
  defaults: {}
});

const form = reactive({
  ticker: "NVDA",
  trade_date: today,
  analysts: ["market", "news", "fundamentals"],
  research_depth: 1,
  llm_provider: "openai",
  quick_think_llm: "deepseek-chat",
  deep_think_llm: "deepseek-reasoner",
  output_language: "Chinese",
  checkpoint_enabled: false
});

const healthLabel = computed(() => t(`health.${healthState.value}`));
const analystLabels = computed(() => ({
  market: t("analyst.market"),
  social: t("analyst.social"),
  news: t("analyst.news"),
  fundamentals: t("analyst.fundamentals")
}));
const reportLabels = computed(() => ({
  market_report: t("report.market"),
  sentiment_report: t("report.sentiment"),
  news_report: t("report.news"),
  fundamentals_report: t("report.fundamentals"),
  investment_plan: t("report.research"),
  trader_investment_plan: t("report.trader"),
  final_trade_decision: t("report.decision")
}));
const statusLabels = computed(() => ({
  queued: t("status.queued"),
  running: t("status.running"),
  completed: t("status.completed"),
  failed: t("status.failed")
}));

const reportTabs = computed(() => {
  const reports = currentJob.value?.result?.reports || {};
  return Object.keys(reportLabels.value)
    .filter((key) => reports[key])
    .map((key) => ({ key, label: reportLabels.value[key] }));
});

const activeReport = computed(() => {
  if (!activeReportKey.value) {
    return "";
  }
  return currentJob.value?.result?.reports?.[activeReportKey.value] || "";
});

const tickerSearchIndex = computed(() => {
  const bySymbol = new Map();
  aShareSearchData.forEach((stock) => {
    const normalizedSymbol = String(stock.symbol || "").toUpperCase();
    if (!normalizedSymbol) {
      return;
    }
    bySymbol.set(normalizedSymbol, {
      symbol: normalizedSymbol,
      code: String(stock.code || normalizedSymbol.split(".")[0]),
      name: String(stock.name || normalizedSymbol),
      aliases: new Set([normalizedSymbol, String(stock.code || ""), String(stock.name || "")].filter(Boolean))
    });
  });

  Object.entries(options.ticker_aliases || {}).forEach(([alias, symbol]) => {
    const normalizedSymbol = String(symbol || "").toUpperCase();
    if (!normalizedSymbol) {
      return;
    }
    const current = bySymbol.get(normalizedSymbol) || {
      symbol: normalizedSymbol,
      code: normalizedSymbol.split(".")[0],
      name: "",
      aliases: new Set([normalizedSymbol])
    };
    const aliasText = String(alias || "").trim();
    if (aliasText) {
      current.aliases.add(aliasText);
      if (hasChinese(aliasText) && !/[0-9.]/.test(aliasText)) {
        if (!current.name || aliasText.length < current.name.length) {
          current.name = aliasText;
        }
      }
    }
    bySymbol.set(normalizedSymbol, current);
  });

  return Array.from(bySymbol.values()).map((item) => {
    const displayName = item.name || item.symbol;
    const fullPinyin = hasChinese(displayName)
      ? pinyin(displayName, { toneType: "none", type: "array" }).join("").toLowerCase()
      : "";
    const initials = hasChinese(displayName)
      ? pinyin(displayName, { pattern: "first", toneType: "none", type: "array" }).join("").toUpperCase()
      : item.code;
    return {
      ...item,
      name: displayName,
      fullPinyin,
      initials,
      searchText: [
        item.symbol,
        item.code,
        displayName,
        fullPinyin,
        initials,
        ...item.aliases
      ]
        .join(" ")
        .toLowerCase()
    };
  });
});

const tickerSuggestions = computed(() => {
  const query = compactTickerInput(form.ticker).toLowerCase();
  if (!query || query.length < 2) {
    return [];
  }
  const queryUpper = query.toUpperCase();
  return tickerSearchIndex.value
    .filter((item) => item.searchText.includes(query) || item.initials.includes(queryUpper))
    .sort((a, b) => tickerMatchRank(a, query, queryUpper) - tickerMatchRank(b, query, queryUpper))
    .slice(0, 8);
});

const selectedTickerPreview = computed(() => {
  const value = form.ticker.trim().toUpperCase();
  if (!value) {
    return null;
  }
  return tickerSearchIndex.value.find((item) => item.symbol === value) || null;
});

const tickerLookup = computed(() => {
  const lookup = new Map();
  tickerSearchIndex.value.forEach((item) => {
    lookup.set(item.symbol, item);
    lookup.set(item.code, item);
  });
  return lookup;
});

const stats = computed(() => {
  const total = jobs.value.length;
  const completed = countByStatus("completed");
  const failed = countByStatus("failed");
  const active = countByStatus("queued") + countByStatus("running");
  const durations = jobs.value
    .filter((job) => job.status === "completed")
    .map(durationMs)
    .filter((value) => value > 0);
  const averageMs = durations.length
    ? durations.reduce((sum, value) => sum + value, 0) / durations.length
    : 0;

  return {
    total,
    completed,
    failed,
    active,
    completionRate: total ? Math.round((completed / total) * 100) : 0,
    averageDuration: formatDuration(averageMs)
  };
});

const statusSegments = computed(() => {
  const base = [
    { key: "completed", label: t("status.completed"), count: countByStatus("completed") },
    { key: "running", label: t("status.running"), count: countByStatus("running") },
    { key: "queued", label: t("status.queued"), count: countByStatus("queued") },
    { key: "failed", label: t("status.failed"), count: countByStatus("failed") }
  ];
  return base.map((item) => ({
    ...item,
    percent: stats.value.total ? Math.round((item.count / stats.value.total) * 100) : 0
  }));
});

const analystUsage = computed(() => {
  const counts = Object.fromEntries(options.analysts.map((key) => [key, 0]));
  jobs.value.forEach((job) => {
    (job.request.analysts || []).forEach((key) => {
      counts[key] = (counts[key] || 0) + 1;
    });
  });
  const max = Math.max(1, ...Object.values(counts));
  return Object.entries(counts).map(([key, count]) => ({
    key,
    label: analystLabels.value[key] || key,
    count,
    percent: Math.round((count / max) * 100)
  }));
});

const providerUsage = computed(() => buildUsage((job) => job.request.llm_provider || options.defaults.llm_provider || t("common.default")));
const tickerUsage = computed(() => buildUsage((job) => job.request.ticker));
const topProvider = computed(() => providerUsage.value[0] || { label: t("common.none"), count: 0 });
const topTicker = computed(() => tickerUsage.value[0] || { label: t("common.none"), count: 0 });
const recentJobs = computed(() => jobs.value.slice(0, 8));

watch(reportTabs, (tabs) => {
  if (tabs.length > 0 && !tabs.some((tab) => tab.key === activeReportKey.value)) {
    activeReportKey.value = tabs[0].key;
  }
});

watch(tickerSuggestions, (suggestions) => {
  if (highlightedTickerSuggestion.value >= suggestions.length) {
    highlightedTickerSuggestion.value = 0;
  }
});

function countByStatus(status) {
  return jobs.value.filter((job) => job.status === status).length;
}

function t(key, params = {}) {
  const template = messages[activeLocale.value]?.[key] ?? messages["en-US"][key] ?? key;
  return Object.entries(params).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template
  );
}

function setLocale(locale) {
  activeLocale.value = locale;
  localStorage.setItem(LOCALE_STORAGE, locale);
}

function durationMs(job) {
  const start = Date.parse(job.started_at || job.created_at || "");
  const end = Date.parse(job.completed_at || job.updated_at || "");
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) {
    return 0;
  }
  return end - start;
}

function formatDuration(ms) {
  if (!ms) {
    return t("duration.zero");
  }
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes <= 0) {
    return t("duration.seconds", { seconds });
  }
  return t("duration.minutes", { minutes, seconds });
}

function buildUsage(getKey) {
  const counts = {};
  jobs.value.forEach((job) => {
    const key = getKey(job) || "unknown";
    counts[key] = (counts[key] || 0) + 1;
  });
  const max = Math.max(1, ...Object.values(counts));
  return Object.entries(counts)
    .map(([key, count]) => ({
      key,
      label: key,
      count,
      percent: Math.round((count / max) * 100)
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

function hasChinese(value) {
  return /[\u4e00-\u9fff]/.test(value);
}

function tickerMatchRank(item, query, queryUpper) {
  if (item.symbol.toLowerCase() === query || item.code === query) {
    return 0;
  }
  if (item.symbol.toLowerCase().startsWith(query) || item.code.startsWith(query)) {
    return 1;
  }
  if (item.initials === queryUpper) {
    return 2;
  }
  if (item.initials.startsWith(queryUpper)) {
    return 3;
  }
  if (item.name.toLowerCase().includes(query)) {
    return 4;
  }
  if (item.fullPinyin.startsWith(query)) {
    return 5;
  }
  return 9;
}

function tickerDisplayName(ticker) {
  const value = String(ticker || "").trim().toUpperCase();
  if (!value) {
    return "";
  }
  return tickerLookup.value.get(value)?.name || "";
}

function formatTickerSubtitle(ticker, tradeDate) {
  const name = tickerDisplayName(ticker);
  return name ? `${name} · ${tradeDate}` : tradeDate;
}

function openTickerSearch() {
  tickerSearchOpen.value = true;
}

function closeTickerSearchSoon() {
  setTimeout(() => {
    tickerSearchOpen.value = false;
  }, 120);
}

function moveTickerHighlight(direction) {
  if (!tickerSearchOpen.value) {
    tickerSearchOpen.value = true;
  }
  const count = tickerSuggestions.value.length;
  if (!count) {
    return;
  }
  highlightedTickerSuggestion.value = (highlightedTickerSuggestion.value + direction + count) % count;
}

function selectTickerSuggestion(item) {
  form.ticker = item.symbol;
  highlightedTickerSuggestion.value = 0;
  tickerSearchOpen.value = false;
}

function bestTickerSuggestion(value) {
  const query = compactTickerInput(value).toLowerCase();
  if (!query || query.length < 2) {
    return null;
  }
  const queryUpper = query.toUpperCase();
  return tickerSearchIndex.value
    .filter((item) => item.searchText.includes(query) || item.initials.includes(queryUpper))
    .sort((a, b) => tickerMatchRank(a, query, queryUpper) - tickerMatchRank(b, query, queryUpper))[0] || null;
}

function handleTickerEnter(event) {
  const suggestion = tickerSuggestions.value[highlightedTickerSuggestion.value] || tickerSuggestions.value[0];
  if (tickerSearchOpen.value && suggestion) {
    event.preventDefault();
    selectTickerSuggestion(suggestion);
  }
}

function persistApiKey() {
  setStoredApiKey(apiKey.value);
  notice.value = t("notice.apiKeySaved");
  setTimeout(() => {
    notice.value = "";
  }, 2500);
}

async function checkHealth() {
  try {
    await getHealth();
    healthState.value = "ok";
  } catch {
    healthState.value = "down";
  }
}

async function loadOptions() {
  try {
    const payload = await apiRequest("/options");
    Object.assign(options, payload);
    form.llm_provider = payload.defaults.llm_provider || form.llm_provider;
    form.quick_think_llm = payload.defaults.quick_think_llm || form.quick_think_llm;
    form.deep_think_llm = payload.defaults.deep_think_llm || form.deep_think_llm;
    form.output_language = payload.defaults.output_language || form.output_language;
  } catch (err) {
    error.value = err.message;
  }
}

async function refreshJobs() {
  try {
    jobs.value = await apiRequest("/analyses");
    if (currentJob.value) {
      const latest = jobs.value.find((job) => job.id === currentJob.value.id);
      if (latest) {
        currentJob.value = latest;
      }
    } else if (jobs.value.length > 0) {
      currentJob.value = jobs.value[0];
    }
  } catch (err) {
    error.value = err.message;
  }
}

async function selectJob(jobId) {
  try {
    currentJob.value = await apiRequest(`/analyses/${jobId}`);
    activeView.value = "console";
  } catch (err) {
    error.value = err.message;
  }
}

async function submitAnalysis() {
  error.value = "";
  notice.value = "";
  submitting.value = true;
  try {
    const payload = {
      ...form,
      ticker: resolveTickerInput(form.ticker),
      analysts: [...form.analysts]
    };
    const job = await apiRequest("/analyses", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    currentJob.value = job;
    notice.value = t("notice.jobSubmitted");
    await refreshJobs();
    startPolling();
  } catch (err) {
    error.value = err.message;
  } finally {
    submitting.value = false;
  }
}

function compactTickerInput(value) {
  return value
    .trim()
    .replaceAll(" ", "")
    .replaceAll("\t", "")
    .replaceAll("（", "(")
    .replaceAll("）", ")")
    .replaceAll("。", ".");
}

function resolveTickerInput(value) {
  const raw = value.trim();
  const compact = compactTickerInput(raw);
  const aliases = options.ticker_aliases || {};
  const candidates = [raw, raw.toUpperCase(), compact, compact.toUpperCase()];
  for (const key of candidates) {
    if (aliases[key]) {
      return aliases[key].toUpperCase();
    }
  }

  const suggestion = bestTickerSuggestion(raw);
  if (suggestion) {
    return suggestion.symbol;
  }

  const embedded = compact.match(/[A-Za-z0-9^][A-Za-z0-9._\-^]{1,31}/);
  if (embedded) {
    const token = embedded[0].toUpperCase();
    return aliases[token] ? aliases[token].toUpperCase() : token;
  }

  if (!/^[A-Za-z0-9._\-^]+$/.test(raw)) {
    throw new Error(t("error.invalidTicker"));
  }
  return raw.toUpperCase();
}

async function deleteCurrentJob() {
  if (!currentJob.value) {
    return;
  }
  try {
    await apiRequest(`/analyses/${currentJob.value.id}`, { method: "DELETE" });
    currentJob.value = null;
    await refreshJobs();
  } catch (err) {
    error.value = err.message;
  }
}

function startPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
  pollTimer = setInterval(async () => {
    await refreshJobs();
    const hasActive = jobs.value.some((job) => ["queued", "running"].includes(job.status));
    if (!hasActive && pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }, 3000);
}

onMounted(async () => {
  await checkHealth();
  await loadOptions();
  await refreshJobs();
  startPolling();
});

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
  }
});
</script>
