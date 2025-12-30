<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand">
        <span class="dot" />
        <h1>Weather Agent Platform</h1>
      </div>
      <nav class="nav">
        <button :class="{ active: activeTab === 'chat' }" @click="activeTab = 'chat'">AI 对话</button>
        <button :class="{ active: activeTab === 'dashboard' }" @click="activeTab = 'dashboard'">数据看板</button>
        <button @click="openBackend('/health')">Health</button>
        <button @click="openBackend('/weather/stats')">Stats</button>
        <button @click="openBackend('/weather?city=北京&limit=20')">Sample (北京)</button>
      </nav>
    </header>
    <main class="content">
      <AgentChat v-if="activeTab === 'chat'" />
      <WeatherDashboard v-else />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import WeatherDashboard from './views/WeatherDashboard.vue';
import AgentChat from './views/AgentChat.vue';

const activeTab = ref('chat');
const BACKEND_BASE = 'http://localhost:8080';
const openBackend = (path) => {
  const url = `${BACKEND_BASE}${path}`;
  window.open(url, '_blank');
};
</script>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.08), transparent 35%),
    radial-gradient(circle at 80% 0%, rgba(14, 165, 233, 0.08), transparent 30%),
    #f6f8fc;
  color: #0f172a;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

.topbar {
  padding: 14px 22px;
  background: linear-gradient(135deg, #0f172a, #111827);
  color: #f8fafc;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22d3ee, #6366f1);
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.6);
}

.brand h1 {
  margin: 0;
  font-size: 18px;
  letter-spacing: 0.3px;
}

.nav {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.nav button {
  height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  color: #e5e7eb;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
}

.nav button.active {
  background: #22d3ee;
  color: #0f172a;
  border-color: #22d3ee;
}

.nav button:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
}

.content {
  flex: 1;
  padding: 18px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}
</style>
