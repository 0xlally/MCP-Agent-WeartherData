import { ref } from 'vue';

// 全局 UI 与跨页面共享数据
export const activeTab = ref('chat');

// 数据 Agent 结果（原始行数据数组）
export const dataRows = ref([]);

// 分析 Agent 结果（如 analysis_group_by_period 的 series 数组）
export const analysisSeries = ref([]);

// 最近一次分析结果和工具名，便于看板根据不同工具渲染不同图表
export const lastAnalysisResult = ref(null); // 保存完整返回对象
export const lastAnalysisTool = ref('');     // 如 analysis.group_by_period
