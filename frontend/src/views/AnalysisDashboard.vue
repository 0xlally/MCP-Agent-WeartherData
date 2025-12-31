<template>
  <div class="card">
    <h2 class="card-title">Analysis Dashboard</h2>
    <form class="filters" @submit.prevent="handleSearch">
      <label>
        City
        <input v-model="city" type="text" placeholder="e.g. Beijing" required />
      </label>
      <label>
        Metric
        <select v-model="metric">
          <option value="temp_max">Max Temperature</option>
          <option value="temp_min">Min Temperature</option>
        </select>
      </label>
      <label>
        Period
        <select v-model="period">
          <option value="year">Year</option>
          <option value="month">Month</option>
        </select>
      </label>
      <label>
        Start Date
        <input v-model="startDate" type="date" />
      </label>
      <label>
        End Date
        <input v-model="endDate" type="date" />
      </label>
      <button type="submit" :disabled="loading">{{ loading ? 'Loading...' : 'Analyze' }}</button>
    </form>

    <section class="chart" ref="chartRef" v-if="showMainChart"></section>
    <p v-else-if="analysisTool === 'analysis.group_by_period'" class="empty">No analysis result yet. Try running an analysis.</p>

    <section v-if="compareRows.length" :key="analysisTool + '-compare'" class="chart" ref="compareChartRef"></section>
    <section v-if="analysisTool === 'analysis.simple_forecast'" class="chart" ref="forecastChartRef"></section>

    <div v-if="analysisTool === 'analysis.describe_timeseries' && analysisResult" class="cards">
      <div class="stat-card">
        <div class="label">Count</div>
        <div class="value">{{ analysisResult.count ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">Min</div>
        <div class="value">{{ analysisResult.min ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">Max</div>
        <div class="value">{{ analysisResult.max ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">Mean</div>
        <div class="value">{{ analysisResult.mean != null ? analysisResult.mean.toFixed(2) : '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">Stddev</div>
        <div class="value">{{ analysisResult.stddev != null ? analysisResult.stddev.toFixed(2) : '-' }}</div>
      </div>
    </div>

    <div v-if="analysisTool === 'analysis.extreme_event_stats' && analysisResult" class="cards">
      <div class="stat-card">
        <div class="label">Event Days</div>
        <div class="value">{{ analysisResult.event_days ?? 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="label">Threshold</div>
        <div class="value">{{ analysisResult.comparison }} {{ analysisResult.threshold }}</div>
      </div>
      <div class="stat-card">
        <div class="label">City</div>
        <div class="value">{{ analysisResult.city }}</div>
      </div>
    </div>

    <table class="table" v-if="analysisTool === 'analysis.group_by_period' && pagedSeries.length">
      <thead>
        <tr>
          <th>Period</th>
          <th>Count</th>
          <th>Min</th>
          <th>Max</th>
          <th>Mean</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in pagedSeries" :key="row.period">
          <td>{{ row.period }}</td>
          <td>{{ row.count }}</td>
          <td>{{ row.min }}</td>
          <td>{{ row.max }}</td>
          <td>{{ row.mean != null ? row.mean.toFixed(2) : '-' }}</td>
        </tr>
      </tbody>
    </table>

    <table class="table" v-if="compareRows.length">
      <thead>
        <tr>
          <th>City</th>
          <th>Count</th>
          <th>Min</th>
          <th>Max</th>
          <th>Mean</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in compareRows" :key="row.city">
          <td>{{ row.city }}</td>
          <td>{{ row.count }}</td>
          <td>{{ row.min }}</td>
          <td>{{ row.max }}</td>
          <td>{{ row.mean != null ? row.mean.toFixed(2) : '-' }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="series.length > pageSize" class="pagination">
      <button :disabled="page === 1" @click="page--">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="page++">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import { callTool } from '../api/agent.js';
import { analysisSeries, lastAnalysisResult, lastAnalysisTool } from '../store/uiStore.js';

const city = ref('北京');
const metric = ref('temp_max');
const period = ref('year');
const startDate = ref('');
const endDate = ref('');
const loading = ref(false);
const series = ref([]);
const chartRef = ref(null);
const compareChartRef = ref(null);
const forecastChartRef = ref(null);
let chartInstance = null;
let compareChartInstance = null;
let forecastChartInstance = null;

const pageSize = 20;
const page = ref(1);
const analysisTool = ref('');
const analysisResult = ref(null);

const showMainChart = computed(() => analysisTool.value === 'analysis.group_by_period' && series.value.length > 0);
const compareRows = computed(() => {
  const rows = analysisResult.value?.results;
  return Array.isArray(rows) ? rows : [];
});

const totalPages = computed(() => {
  return series.value.length ? Math.ceil(series.value.length / pageSize) : 1;
});

const pagedSeries = computed(() => {
  const start = (page.value - 1) * pageSize;
  return series.value.slice(start, start + pageSize);
});

const buildOption = (data) => {
  const labels = data.map((d) => d.period);
  const means = data.map((d) => d.mean);
  const mins = data.map((d) => d.min);
  const maxs = data.map((d) => d.max);
  const counts = data.map((d) => d.count);

  return {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const idx = params[0]?.dataIndex ?? 0;
        const row = data[idx] || {};
        return [
          `${row.period}`,
          `Count: ${row.count}`,
          `Min: ${row.min}`,
          `Max: ${row.max}`,
          `Mean: ${row.mean != null ? row.mean.toFixed(2) : '-'}`
        ].join('<br/>');
      }
    },
    legend: { data: ['Mean (bar)', 'Max', 'Min', 'Count'] },
    grid: { left: 60, right: 60, bottom: 60, top: 40 },
    xAxis: { type: 'category', data: labels },
    yAxis: [
      { type: 'value', name: '°C' },
      { type: 'value', name: 'Count', position: 'right' }
    ],
    series: [
      { name: 'Mean (bar)', type: 'bar', data: means, itemStyle: { color: '#22d3ee' } },
      { name: 'Max', type: 'line', smooth: true, data: maxs, itemStyle: { color: '#f97316' } },
      { name: 'Min', type: 'line', smooth: true, data: mins, itemStyle: { color: '#3b82f6' } },
      { name: 'Count', type: 'bar', yAxisIndex: 1, data: counts, itemStyle: { color: '#94a3b8', opacity: 0.6 } }
    ]
  };
};

const renderChart = () => {
  if (!chartRef.value || analysisTool.value !== 'analysis.group_by_period' || !series.value.length) return;
  nextTick(() => {
    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value);
    }
    chartInstance.setOption(buildOption(series.value), true);
    chartInstance.resize();
  });
};

const renderCompareChart = () => {
  if (!compareChartRef.value) return;
  const results = compareRows.value;
  if (!results.length) {
    if (compareChartInstance) compareChartInstance.clear();
    return;
  }
  nextTick(() => {
    // 强制重新初始化以避免旧实例尺寸问题
    if (compareChartInstance) {
      compareChartInstance.dispose();
    }
    compareChartInstance = echarts.init(compareChartRef.value);
    const cities = results.map((r) => r.city);
    const means = results.map((r) => r.mean ?? null);
    const maxs = results.map((r) => r.max ?? null);
    const mins = results.map((r) => r.min ?? null);
    compareChartInstance.setOption({
      backgroundColor: '#ffffff',
      tooltip: { trigger: 'axis' },
      legend: { data: ['Mean', 'Max', 'Min'] },
      grid: { left: 60, right: 40, bottom: 60, top: 40 },
      xAxis: { type: 'category', data: cities },
      yAxis: { type: 'value', name: '°C' },
      series: [
        { name: 'Mean', type: 'bar', data: means, label: { show: true, position: 'top' } },
        { name: 'Max', type: 'line', data: maxs },
        { name: 'Min', type: 'line', data: mins }
      ]
    }, true);
    compareChartInstance.resize({
      width: compareChartRef.value?.clientWidth,
      height: compareChartRef.value?.clientHeight,
    });
  });
};

const renderForecastChart = () => {
  if (!forecastChartRef.value || analysisTool.value !== 'analysis.simple_forecast') return;
  const fc = analysisResult.value?.forecast || [];
  if (!fc.length) return;
  nextTick(() => {
    if (!forecastChartInstance) forecastChartInstance = echarts.init(forecastChartRef.value);
    const dates = fc.map((d) => d.date);
    const metricKey = analysisResult.value?.metric || 'temp_max';
    const vals = fc.map((d) => d[metricKey]);
    forecastChartInstance.setOption({
      backgroundColor: '#ffffff',
      tooltip: { trigger: 'axis' },
      legend: { data: ['Forecast'] },
      grid: { left: 60, right: 40, bottom: 60, top: 40 },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: '°C' },
      series: [
        { name: 'Forecast', type: 'line', smooth: true, data: vals }
      ]
    }, true);
    forecastChartInstance.resize();
  });
};

const resizeChart = () => {
  if (chartInstance) chartInstance.resize();
  if (compareChartInstance) compareChartInstance.resize();
  if (forecastChartInstance) forecastChartInstance.resize();
};

const handleSearch = async () => {
  loading.value = true;
  page.value = 1;
  try {
    const payload = {
      city: city.value,
      metric: metric.value,
      period: period.value,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined
    };
    const result = await callTool('analysis_group_by_period', payload);
    series.value = Array.isArray(result?.series) ? result.series : [];
    analysisSeries.value = series.value;
    analysisResult.value = result;
    analysisTool.value = 'analysis.group_by_period';
    renderChart();
  } catch (err) {
    console.error('Failed to run analysis_group_by_period', err);
    series.value = [];
    renderChart();
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // 如果有来自 Agent 的共享分析结果，优先展示
  if (Array.isArray(analysisSeries.value) && analysisSeries.value.length) {
    series.value = analysisSeries.value;
  }
  if (lastAnalysisResult.value) {
    analysisResult.value = lastAnalysisResult.value;
    // 优先使用已存的工具名，否则根据结果推断
    if (lastAnalysisTool.value) {
      analysisTool.value = lastAnalysisTool.value;
    } else if (Array.isArray(lastAnalysisResult.value?.results)) {
      analysisTool.value = 'analysis.compare_cities';
    } else {
      analysisTool.value = 'analysis.group_by_period';
    }
    if (analysisTool.value !== 'analysis.group_by_period') {
      // avoid rendering the main chart with incompatible data
      series.value = analysisSeries.value = [];
    }
  }
  window.addEventListener('resize', resizeChart);
  nextTick(() => {
    renderChart();
    renderCompareChart();
    renderForecastChart();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
  if (compareChartInstance) {
    compareChartInstance.dispose();
    compareChartInstance = null;
  }
  if (forecastChartInstance) {
    forecastChartInstance.dispose();
    forecastChartInstance = null;
  }
});

watch(series, () => {
  // series 变化时重绘
  if (!series.value.length && chartInstance) {
    chartInstance.clear();
  } else {
    renderChart();
  }
});

watch(analysisTool, () => {
  // 工具切换时重新绘制对应图表
  if (analysisTool.value !== 'analysis.compare_cities' && compareChartInstance) {
    compareChartInstance.dispose();
    compareChartInstance = null;
  }
  if (analysisTool.value !== 'analysis.group_by_period' && chartInstance) {
    chartInstance.clear();
  }
  renderChart();
  renderCompareChart();
  renderForecastChart();
});

watch(analysisResult, () => {
  // 结果更新时刷新图表
  renderCompareChart();
  renderForecastChart();
});

watch(compareRows, () => {
  // 比较结果变化时刷新对比图
  renderCompareChart();
});

watch(page, () => {
  // 翻页时无需重绘图表，但需要保证页码不越界
  if (page.value < 1) page.value = 1;
  if (page.value > totalPages.value) page.value = totalPages.value;
});

watch(analysisSeries, (val) => {
  series.value = analysisTool.value === 'analysis.group_by_period' ? (Array.isArray(val) ? val : []) : [];
});

watch(lastAnalysisResult, (val) => {
  analysisResult.value = val;
  if (analysisTool.value !== 'analysis.group_by_period') {
    series.value = [];
  }
});

watch(lastAnalysisTool, (val) => {
  analysisTool.value = val;
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
  margin: 0 0 12px;
  font-size: 20px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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

.filters input,
.filters select {
  height: 36px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s ease;
}

.filters input:focus,
.filters select:focus {
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

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin: 12px 0 8px;
}

.stat-card {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
}

.stat-card .label {
  color: #6b7280;
  font-size: 12px;
}

.stat-card .value {
  font-size: 18px;
  font-weight: 700;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  margin-top: 8px;
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
  font-size: 14px;
}

.pagination button {
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
