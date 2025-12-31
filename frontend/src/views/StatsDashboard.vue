<template>
  <div class="card">
    <h2 class="card-title">System & Data Stats</h2>

    <section v-if="loading" class="section">
      <p>Loading stats...</p>
    </section>

    <section v-else class="grid">
      <div class="section">
        <h3>Health</h3>
        <p class="status" :class="health.status === 'healthy' ? 'ok' : 'bad'">
          {{ health.status || 'unknown' }}
        </p>
        <p v-if="health.version" class="muted">Version: {{ health.version }}</p>
      </div>

      <div class="section">
        <h3>Data Volume</h3>
        <p class="big">{{ stats.total_records?.toLocaleString() || '-' }}</p>
        <p class="muted">Total weather records</p>
      </div>

      <div class="section">
        <h3>Cities</h3>
        <p class="big">{{ stats.cities_count ?? '-' }}</p>
        <p class="muted">Cities with data</p>
        <div v-if="stats.cities?.length" class="chips">
          <span v-for="c in stats.cities" :key="c" class="chip">{{ c }}</span>
        </div>
      </div>

      <div class="section">
        <h3>Date Range</h3>
        <p v-if="stats.date_range?.start && stats.date_range?.end" class="range">
          {{ stats.date_range.start }} → {{ stats.date_range.end }}
        </p>
        <p v-else class="muted">No date range info</p>
      </div>
    </section>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api/client.js';

const loading = ref(false);
const error = ref('');
const health = ref({});
const stats = ref({});

const loadStats = async () => {
  loading.value = true;
  error.value = '';
  try {
    const [healthResp, statsResp] = await Promise.all([
      api.get('/health'),
      api.get('/weather/stats')
    ]);
    health.value = healthResp.data || {};
    stats.value = statsResp.data || {};
  } catch (e) {
    console.error('Failed to load stats', e);
    error.value = '加载统计信息失败，请稍后重试。';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadStats();
});
</script>

<style scoped>
.card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.card-title {
  margin: 0 0 16px;
  font-size: 20px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.section {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}

.section h3 {
  margin: 0 0 8px;
  font-size: 15px;
}

.status {
  font-weight: 700;
  font-size: 16px;
}

.status.ok {
  color: #16a34a;
}

.status.bad {
  color: #dc2626;
}

.big {
  font-size: 24px;
  font-weight: 700;
}

.muted {
  color: #6b7280;
  font-size: 13px;
}

.chips {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 2px 8px;
  border-radius: 999px;
  background: #e0f2fe;
  color: #0369a1;
  font-size: 12px;
}

.range {
  font-weight: 600;
}

.error {
  margin-top: 12px;
  color: #dc2626;
  font-size: 13px;
}
</style>
