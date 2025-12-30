<template>
  <div class="chat-layout">
    <section class="chat-panel">
      <header class="chat-header">
        <div>
          <p class="eyebrow">Weather Data Agent</p>
          <h2>AI 对话助手</h2>
          <p class="sub">输入需求 → 云端 LLM 规划工具 → 调用本地 MCP HTTP 端 → 返回 JSON 结果</p>
        </div>
        <div class="llm-config">
          <input v-model="llmBaseUrl" type="text" placeholder="LLM API Base (可选，如 https://api.openai.com/v1)" />
          <input v-model="llmApiKey" type="password" placeholder="LLM API Key (保存在本地浏览器)" />
          <button @click="saveLlmcfg">保存配置</button>
        </div>
      </header>

      <div class="chat-window" ref="scrollRef">
        <div v-for="(m, idx) in messages" :key="idx" class="msg" :class="m.role">
          <div class="badge">{{ m.role === 'user' ? 'User' : 'Assistant' }}</div>
          <pre class="bubble">{{ m.content }}</pre>
        </div>
      </div>

      <form class="composer" @submit.prevent="handleSend">
        <textarea v-model="input" rows="3" placeholder="例如：帮我看下北京 2025-11-01 到 2025-11-15 的天气，列出每天最高温" />
        <div class="actions">
          <button type="submit" :disabled="loading || !input.trim()">{{ loading ? '处理中...' : '发送' }}</button>
          <button type="button" :disabled="!downloadable" @click="downloadJson">下载 JSON</button>
        </div>
      </form>
    </section>

    <section class="side-panel">
      <div class="block">
        <h3>当前工具计划</h3>
        <pre class="mini" v-if="plan">{{ JSON.stringify(plan, null, 2) }}</pre>
        <p v-else class="hint">等待新对话</p>
      </div>

      <div class="block">
        <h3>可用 MCP 工具</h3>
        <div v-if="toolList.length" class="tool-list">
          <div v-for="t in toolList" :key="t.name" class="tool-item">
            <strong>{{ t.name }}</strong>
            <div class="desc">{{ t.description }}</div>
            <div class="params" v-if="t.params">{{ JSON.stringify(t.params) }}</div>
          </div>
        </div>
        <p v-else class="hint">加载中或未获取到列表</p>
      </div>

      <div class="block" v-if="lastResult">
        <h3>最新结果（摘录）</h3>
        <pre class="mini">{{ previewResult }}</pre>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref, nextTick, computed } from 'vue';
import { listTools, callTool } from '../api/agent.js';

const DEFAULT_LLM_BASE = import.meta.env.VITE_LLM_BASE || 'https://api.deepseek.com/v1';
const DEFAULT_LLM_KEY = import.meta.env.VITE_LLM_KEY || '';

const input = ref('');
const loading = ref(false);
const messages = ref([
  { role: 'assistant', content: '你好，我是天气数据代理。请告诉我城市、日期范围或你要的统计，我会调用合适的工具。' }
]);
const toolList = ref([]);
const plan = ref(null);
const lastResult = ref(null);
const downloadPayload = ref(null);
const llmBaseUrl = ref(localStorage.getItem('llm_base') || DEFAULT_LLM_BASE);
const llmApiKey = ref(localStorage.getItem('llm_key') || DEFAULT_LLM_KEY);
const scrollRef = ref(null);

const downloadable = computed(() => Array.isArray(downloadPayload.value) && downloadPayload.value.length > 0);
const previewResult = computed(() => {
  if (!lastResult.value) return '';
  return JSON.stringify(lastResult.value, null, 2).slice(0, 900);
});

const saveLlmcfg = () => {
  localStorage.setItem('llm_base', llmBaseUrl.value || '');
  localStorage.setItem('llm_key', llmApiKey.value || '');
};

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
    }
  });
};

const fetchTools = async () => {
  try {
    const { data } = await listTools();
    const flat = [];
    Object.values(data?.tools || {}).forEach((arr) => {
      (arr || []).forEach((t) => flat.push(t));
    });
    toolList.value = flat;
  } catch (e) {
    console.error('Failed to load tools', e);
  }
};

const heuristicPlan = (prompt) => {
  const lower = prompt.toLowerCase();
  if (lower.includes('概览') || lower.includes('overview') || lower.includes('总览')) {
    return { tool: 'data_get_dataset_overview', arguments: {} };
  }
  if (lower.includes('覆盖') || lower.includes('缺失') || lower.includes('missing')) {
    return { tool: 'data_check_coverage', arguments: {} };
  }
  return { tool: 'data_get_range', arguments: {} };
};

const safeParseJson = (raw) => {
  if (!raw) throw new Error('LLM 返回为空');
  const trimmed = raw.trim()
    .replace(/^```json\s*/i, '')
    .replace(/^```/i, '')
    .replace(/```\s*$/i, '')
    .trim();
  return JSON.parse(trimmed);
};

const callLlmForPlan = async (prompt) => {
  const base = llmBaseUrl.value || DEFAULT_LLM_BASE;
  const key = llmApiKey.value || DEFAULT_LLM_KEY;

  if (!base || !key) {
    return heuristicPlan(prompt);
  }
  const body = {
    model: 'deepseek-chat',
    messages: [
      {
        role: 'system',
        content:
          'You are a planner. Respond ONLY with JSON like {"tool": "data_get_range", "arguments": {...}}. Tools: data_get_range(city,start_date,end_date,limit), data_get_dataset_overview(), data_check_coverage(city,start_date,end_date), data_custom_query(fields,city,start_date,end_date,limit), data_update_city_range(city,start_date,end_date). Dates must be YYYY-MM-DD.',
      },
      { role: 'user', content: prompt },
    ],
    temperature: 0,
    response_format: { type: 'json_object' },
  };
  const resp = await fetch(`${base}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  const text = data?.choices?.[0]?.message?.content;
  try {
    return safeParseJson(text);
  } catch (err) {
    console.error('LLM parse failed', text, err);
    throw new Error('LLM 返回非 JSON，请重试或检查 API 响应');
  }
};

const normalizeToolName = (name) => {
  if (!name) return '';
  if (name.includes('.')) return name;
  return name.replace('data_get', 'data.get').replace('data_check', 'data.check').replace('data_custom', 'data.custom').replace('data_update', 'data.update');
};

const pickDownloadPayload = (result) => {
  if (!result) return null;
  if (Array.isArray(result.items)) return result.items;
  if (Array.isArray(result.rows)) return result.rows;
  if (Array.isArray(result)) return result;
  return [result];
};

const handleSend = async () => {
  const content = input.value.trim();
  if (!content) return;
  messages.value.push({ role: 'user', content });
  input.value = '';
  loading.value = true;
  scrollToBottom();

  try {
    const planResp = await callLlmForPlan(content);
    plan.value = planResp;
    messages.value.push({ role: 'assistant', content: `使用工具: ${planResp.tool}\n参数: ${JSON.stringify(planResp.arguments || {})}` });
    scrollToBottom();

    const toolName = planResp.tool;
    const payload = planResp.arguments || {};
    const apiTool = normalizeToolName(toolName);
    const result = await callTool(apiTool, payload);
    lastResult.value = result;
    downloadPayload.value = pickDownloadPayload(result);

    const summary = Array.isArray(result?.items)
      ? `共 ${result.items.length} 条`
      : Array.isArray(result?.rows)
      ? `共 ${result.rows.length} 条`
      : '已返回结果';
    messages.value.push({ role: 'assistant', content: `调用完成: ${apiTool}\n${summary}` });
  } catch (err) {
    console.error(err);
    messages.value.push({ role: 'assistant', content: `出错: ${err?.message || err}` });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
};

const downloadJson = () => {
  if (!downloadable.value) return;
  const blob = new Blob([JSON.stringify(downloadPayload.value, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'weather_agent_result.json';
  a.click();
  URL.revokeObjectURL(url);
};

onMounted(() => {
  fetchTools();
});
</script>

<style scoped>
.chat-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 18px;
  padding: 18px;
}

.chat-panel {
  background: #0f172a;
  color: #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #38bdf8;
  font-size: 12px;
}

.chat-header h2 {
  margin: 4px 0;
  font-size: 22px;
}

.sub {
  margin: 0;
  color: #cbd5e1;
}

.llm-config {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 8px;
  min-width: 320px;
}

.llm-config input {
  padding: 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.06);
  color: #e5e7eb;
}

.llm-config button {
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: #22d3ee;
  color: #0f172a;
  font-weight: 700;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
}

.chat-window {
  height: 420px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
}

.msg {
  margin-bottom: 12px;
}

.msg .badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 12px;
  margin-bottom: 6px;
  background: rgba(34, 211, 238, 0.2);
  color: #38bdf8;
}

.msg.user .badge {
  background: rgba(94, 234, 212, 0.2);
  color: #5eead4;
}

.bubble {
  margin: 0;
  white-space: pre-wrap;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 10px;
  color: #e2e8f0;
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

.composer {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.composer textarea {
  width: 100%;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
  color: #e5e7eb;
  padding: 10px;
  resize: vertical;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.actions button {
  border: none;
  border-radius: 10px;
  padding: 10px 16px;
  font-weight: 700;
  cursor: pointer;
}

.actions button:first-of-type {
  background: #22d3ee;
  color: #0f172a;
}

.actions button:last-of-type {
  background: #111827;
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.block {
  background: #ffffff;
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.block h3 {
  margin: 0 0 8px;
}

.hint {
  color: #6b7280;
  margin: 0;
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px;
  background: #f8fafc;
}

.tool-item .desc {
  font-size: 13px;
  color: #374151;
}

.tool-item .params {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
  white-space: pre-wrap;
}

.mini {
  background: #0f172a;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 8px;
  margin: 0;
  overflow: auto;
  max-height: 200px;
  white-space: pre-wrap;
}

@media (max-width: 960px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }
  .llm-config {
    grid-template-columns: 1fr;
  }
}
</style>
