<template>
  <div class="min-h-screen bg-[#0a0a0f] relative">
    <ParticleBackground />
    <header class="border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-xl sticky top-0 z-50 relative">
      <div class="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 group">
          <span class="text-lg font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent group-hover:from-blue-300 group-hover:to-purple-300 transition-all">VoteAI</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 font-medium">BETA</span>
        </router-link>
        <div class="flex items-center gap-3">
          <span class="text-xs text-gray-500">今日剩余 <span class="text-gray-300 font-mono">{{ quotaText }}</span> 次</span>
          <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
          <span class="text-xs text-gray-500">4 模型在线</span>
        </div>
      </div>
    </header>
    <main class="max-w-3xl mx-auto px-6 py-8 relative z-10">
      <router-view @quota-update="fetchQuota" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, provide } from 'vue'
import { getQuota } from './api/index.js'
import ParticleBackground from './components/ParticleBackground.vue'

const quotaText = ref('...')

async function fetchQuota() {
  try {
    const q = await getQuota()
    quotaText.value = q.remaining
  } catch { quotaText.value = '...' }
}

onMounted(fetchQuota)
provide('fetchQuota', fetchQuota)
</script>
