<template>
  <div class="card">
    <h2 class="card-title">Weather Data</h2>
    <form class="filters" @submit.prevent="handleSearch">
      <label>
        City
        <input v-model="city" type="text" placeholder="e.g. Beijing" required />
      </label>
      <label>
        Start Date
        <input v-model="startDate" type="date" />
      </label>
      <label>
        End Date
        <input v-model="endDate" type="date" />
      </label>
      <button type="submit" :disabled="loading">{{ loading ? 'Loading...' : 'Search' }}</button>
    </form>

    <section class="chart" ref="chartRef"></section>

    <table class="table" v-if="rows.length">
      <thead>
        <tr>
          <th>Date</th>
          <th>City</th>
          <th>Min Temp</th>
          <th>Max Temp</th>
          <th>Condition</th>
          <th>Wind</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.date || row.observed_at || '-' }}</td>
          <td>{{ row.city || '-' }}</td>
          <td>{{ row.temp_min ?? row.min_temp ?? row.minTemperature ?? '-' }}</td>
          <td>{{ row.temp_max ?? row.max_temp ?? row.maxTemperature ?? '-' }}</td>
          <td>{{ row.weather_condition || '-' }}</td>
          <td>{{ row.wind_info || '-' }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else class="empty">No data. Try searching.</p>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import * as echarts from 'echarts';
import api from '../api/client.js';

const city = ref('');
const startDate = ref('');
const endDate = ref('');
const loading = ref(false);
const rows = ref([]);
const chartRef = ref(null);
let chartInstance = null;

const buildOption = (data) => {
  const dates = data.map((d) => d.date || d.observed_at || '');
  const minTemps = data.map((d) => d.temp_min ?? d.min_temp ?? d.minTemperature ?? null);
  const maxTemps = data.map((d) => d.temp_max ?? d.max_temp ?? d.maxTemperature ?? null);

  return {
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'axis' },
    legend: { data: ['Min', 'Max'] },
    grid: { left: 60, right: 40, bottom: 60, top: 40 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '°C' },
    series: [
      { name: 'Min', type: 'line', smooth: true, data: minTemps },
      { name: 'Max', type: 'line', smooth: true, data: maxTemps }
    ]
  };
};

const renderChart = () => {
  if (!chartRef.value) return;
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }
  chartInstance.setOption(buildOption(rows.value));
};

const handleSearch = async () => {
  loading.value = true;
  try {
    const params = { city: city.value, start_date: startDate.value, end_date: endDate.value };
    const { data } = await api.get('/weather', { params });
    rows.value = Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : [];
    renderChart();
  } catch (err) {
    console.error('Failed to fetch weather', err);
    rows.value = [];
    renderChart();
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  renderChart();
  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});

const resizeChart = () => {
  if (chartInstance) chartInstance.resize();
};

watch(rows, renderChart);
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
  margin: 0 0 12px;
  font-size: 20px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  align-items: end;
  margin-bottom: 16px;
}

.filters label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  color: #374151;
}

.filters input {
  height: 36px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s ease;
}

.filters input:focus {
  border-color: #2563eb;
}

.filters button {
  height: 38px;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.filters button:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.chart {
  width: 100%;
  height: 340px;
  margin: 12px 0 16px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}

.table th,
.table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}

.table th {
  background: #f8fafc;
  font-weight: 600;
}

.empty {
  color: #6b7280;
  text-align: center;
  margin-top: 12px;
}
</style>
