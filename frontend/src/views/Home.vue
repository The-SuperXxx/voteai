<template>
  <div>
    <!-- Hero -->
    <div class="text-center mb-10 pt-6">
      <h1 class="text-5xl font-black mb-3 tracking-tight">
        <span class="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          VoteAI
        </span>
      </h1>
      <p class="text-gray-500 text-base">智谱 · 千问 三个模型回答，精华合成最优解</p>
    </div>

    <!-- 输入区 -->
    <div class="mb-10">
      <div class="flex gap-2">
        <div class="flex-1 relative">
          <input
            v-model="question"
            @keyup.enter="handleAsk"
            :placeholder="`试试：${currentSuggestion}`"
            class="w-full bg-gray-950/60 backdrop-blur-xl border border-gray-700/50 focus:border-blue-500 rounded-2xl px-5 py-4 text-white placeholder-gray-600 outline-none transition-all text-base pr-12"
            :disabled="loading"
          />
          <button v-if="question && !loading" @click="question = ''" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 text-sm">✕</button>
        </div>
        <button @click="handleAsk" :disabled="loading" class="shrink-0 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-600 text-white px-6 py-4 rounded-2xl font-semibold transition-all text-base disabled:cursor-not-allowed">
          <span v-if="!loading">发送</span>
          <span v-else class="flex items-center gap-2"><span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span></span>
        </button>
      </div>
      <p class="text-xs text-gray-600 mt-2 text-center">3 个 AI 独立回答，裁判 AI 提取精华合成最佳答案</p>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="text-center py-16">
      <div v-if="streaming" class="space-y-4 text-left">
        <div v-for="m in modelNames" :key="m" class="bg-gray-950/60 backdrop-blur-xl border border-gray-800/50 rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full" :class="streamDone[m] ? 'bg-green-400' : 'bg-blue-400 animate-pulse'"></span>
              <span class="text-sm font-medium text-gray-300">{{ m }}</span>
              <span v-if="streamDone[m]" class="text-xs text-green-500">完成</span>
              <span v-else class="text-xs text-gray-500">生成中...</span>
            </div>
            <button @click="toggleStreamExpand(m)" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">
              {{ streamExpanded[m] ? '收起' : '展开' }}
            </button>
          </div>
          <div
            class="text-sm text-gray-400 leading-relaxed whitespace-pre-wrap"
            :class="streamExpanded[m] ? '' : 'max-h-24 overflow-hidden'"
          >
            {{ streamTexts[m] || '' }}<span v-if="!streamDone[m]" class="inline-block w-2 h-4 bg-blue-400 ml-0.5 animate-pulse align-middle"></span>
          </div>
        </div>
        <div v-if="streamStatus === 'synthesizing'" class="text-center py-4">
          <div class="inline-flex items-center gap-2 text-sm text-gray-400">
            <span class="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></span>
            AI 正在综合合成最佳答案...
          </div>
        </div>
      </div>
      <div v-else>
        <div class="inline-flex items-center gap-3 mb-4">
          <span class="w-2.5 h-2.5 rounded-full bg-blue-500 animate-bounce" style="animation-delay:0s"></span>
          <span class="w-2.5 h-2.5 rounded-full bg-purple-500 animate-bounce" style="animation-delay:0.15s"></span>
          <span class="w-2.5 h-2.5 rounded-full bg-pink-500 animate-bounce" style="animation-delay:0.3s"></span>
        </div>
        <p class="text-sm text-gray-500">{{ loadingText }}</p>
      </div>
    </div>

    <!-- 结果 -->
    <div v-if="result && !loading" class="space-y-5 animate-fade-in">
      <div class="bg-gray-950/70 backdrop-blur-xl border border-purple-500/20 rounded-2xl p-6 shadow-xl">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-purple-400"></span>
            <h2 class="text-sm font-semibold text-purple-400 uppercase tracking-wider">综合答案</h2>
            <span class="text-xs text-gray-500 ml-1">三模型精华合成</span>
          </div>
          <button @click="copyAnswer" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">{{ copied ? '已复制' : '复制答案' }}</button>
        </div>
        <div class="text-gray-100 leading-relaxed whitespace-pre-wrap text-[15px]" v-html="renderMarkdown(result.best_answer)"></div>
      </div>

      <div class="bg-gray-950/60 backdrop-blur-xl border border-gray-800/50 rounded-2xl p-5">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">各 AI 原始回答</h3>
        <div class="space-y-3">
          <div v-for="ans in result.all_answers" :key="ans.model" class="bg-gray-950/40 border border-gray-800/30 rounded-xl overflow-hidden">
            <button @click="toggleAnswer(ans.model)" class="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.02] transition-colors">
              <span class="text-sm font-medium text-gray-400">{{ ans.model }}</span>
              <span class="text-xs text-gray-600">{{ expandedAnswers[ans.model] ? '收起 ▲' : '展开 ▼' }}</span>
            </button>
            <div v-show="expandedAnswers[ans.model]" class="px-4 pb-4 text-sm text-gray-400 leading-relaxed whitespace-pre-wrap">{{ ans.answer }}</div>
          </div>
        </div>
      </div>

      <div class="flex justify-center pt-4">
        <button @click="clearResult" class="text-sm text-gray-500 hover:text-gray-300 transition-colors">← 问新问题</button>
      </div>
    </div>

    <!-- 额度用完提示 -->
    <div v-if="limitReached && !loading" class="text-center py-16 animate-fade-in">
      <div class="text-4xl mb-4">🎯</div>
      <h2 class="text-xl font-bold text-white mb-2">今日免费次数已用完</h2>
      <p class="text-gray-500 mb-6">每天 20 次免费提问，明天自动重置</p>
      <div class="inline-flex gap-3">
        <button disabled class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium opacity-50 cursor-not-allowed">¥9.9/月 无限次数</button>
        <button disabled class="px-5 py-2.5 rounded-xl bg-gray-800 text-gray-400 text-sm font-medium cursor-not-allowed">¥1/天</button>
      </div>
      <p class="text-xs text-gray-600 mt-4">付费功能即将上线</p>
    </div>

    <!-- 空状态 -->
    <div v-if="!result && !loading && history.length === 0" class="text-center py-20">
      <p class="text-gray-700 text-lg mb-2">向 VoteAI 提问</p>
      <p class="text-gray-700 text-sm">三个 AI 模型独立回答，再由 AI 裁判合成最佳答案</p>
    </div>

    <!-- 历史记录 -->
    <div v-if="history.length > 0 && !loading && !result" class="mt-12">
      <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">最近提问</h3>
      <div class="space-y-2">
        <div v-for="item in history" :key="item.id" class="flex items-center justify-between bg-gray-950/40 backdrop-blur-xl border border-gray-800/30 rounded-xl px-4 py-3 group hover:bg-gray-900/60 hover:border-gray-700/50 transition-all">
          <div @click="loadHistoryItem(item.id)" class="flex-1 min-w-0 cursor-pointer">
            <p class="text-sm text-gray-300 truncate">{{ item.question }}</p>
            <p class="text-xs text-gray-600 mt-0.5">{{ formatTime(item.created_at) }}</p>
          </div>
          <div class="flex items-center gap-2 ml-3">
            <button @click.stop="deleteHistoryItem(item.id)" class="text-gray-700 hover:text-red-500 transition-colors text-sm opacity-0 group-hover:opacity-100 px-1" title="删除">✕</button>
            <span @click="loadHistoryItem(item.id)" class="text-gray-600 group-hover:text-gray-400 transition-colors text-sm cursor-pointer">→</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { askQuestionStream, getHistory, getResult, deleteResult, getQuota } from '../api/index.js'

const question = ref('')
const loading = ref(false)
const loadingText = ref('')
const result = ref(null)
const expandedAnswers = reactive({})
const history = ref([])
const copied = ref(false)
const streaming = ref(false)
const streamTexts = reactive({})
const streamDone = reactive({})
const streamExpanded = reactive({})
const streamStatus = ref('')
const limitReached = ref(false)
const modelNames = ['GLM-4-Flash', 'GLM-Z1-Flash', 'Qwen-Turbo', 'Kimi']

const suggestedQuestions = [
  'Python 和 Go 哪个更适合做后端？',
  '如何快速入门机器学习？',
  'Vue 和 React 怎么选？',
  '什么是 RAG？通俗解释一下',
  '写一段快速排序的 Python 代码',
  '2026 年 AI 领域最大的突破是什么？',
  '怎么用 Tailwind CSS 做一个好看的按钮？',
  '推荐 3 本适合初学者的编程书',
  'WebSocket 和 SSE 有什么区别？',
  '如何优化 SQL 查询性能？',
]
const currentSuggestion = ref(suggestedQuestions[0])
let suggestionTimer = null

onMounted(async () => {
  try { const data = await getHistory(10); history.value = data.items || [] } catch (e) { /* */ }
  let idx = 0
  suggestionTimer = setInterval(() => { idx = (idx + 1) % suggestedQuestions.length; currentSuggestion.value = suggestedQuestions[idx] }, 5000)
})

onUnmounted(() => { clearInterval(suggestionTimer) })

function renderMarkdown(text) {
  if (!text) return ''
  return text.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/`([^`]+)`/g, '<code class="bg-gray-800 text-blue-300 px-1 py-0.5 rounded text-sm">$1</code>').replace(/\n/g, '<br>')
}

async function handleAsk() {
  if (loading.value) return
  if (!question.value.trim()) question.value = currentSuggestion.value
  loading.value = true
  result.value = null
  streaming.value = true
  streamStatus.value = ''
  for (const m of modelNames) { streamTexts[m] = ''; streamDone[m] = false; streamExpanded[m] = false }
  askQuestionStream(question.value, {
    onToken(model, token) { streamTexts[model] = (streamTexts[model] || '') + token },
    onDone(model) { streamDone[model] = true },
    onStatus(status) { streamStatus.value = status },
    onResult(data) { result.value = data; expandedAnswers[data.best_model] = true; streaming.value = false; loading.value = false; getHistory(10).then(d => { history.value = d.items || [] }); refreshQuota() },
    onError(err) { result.value = { best_answer: `请求失败: ${err}`, best_model: '系统错误', score: 0, votes: [], all_answers: [] }; streaming.value = false; loading.value = false },
    onLimit(msg) { limitReached.value = true; streaming.value = false; loading.value = false },
  })
}

async function loadHistoryItem(id) {
  loading.value = true
  try { const res = await getResult(id); result.value = res; question.value = res.question } catch { result.value = { best_answer: '加载失败' } }
  loading.value = false
}

function toggleAnswer(model) { expandedAnswers[model] = !expandedAnswers[model] }
function toggleStreamExpand(model) { streamExpanded[model] = !streamExpanded[model] }
function clearResult() { result.value = null; question.value = '' }

async function refreshQuota() {
  try { const q = await getQuota(); limitReached.value = q.remaining <= 0 } catch {}
}

async function deleteHistoryItem(id) {
  await deleteResult(id)
  history.value = history.value.filter(h => h.id !== id)
}

async function copyAnswer() {
  try { await navigator.clipboard.writeText(result.value.best_answer); copied.value = true; setTimeout(() => copied.value = false, 2000) } catch { /* */ }
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso), now = new Date(), diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
@keyframes fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-in { animation: fade-in 0.4s ease-out; }
</style>
