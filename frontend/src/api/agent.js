import api from './client.js';

const TOOL_ROUTE = {
  data_get_range: '/mcp/data.get_range',
  data_get_dataset_overview: '/mcp/data.get_dataset_overview',
  data_check_coverage: '/mcp/data.check_coverage',
  data_custom_query: '/mcp/data.custom_query',
  data_update_city_range: '/mcp/data.update_city_range',
  analysis_describe_timeseries: '/mcp/analysis/describe_timeseries',
  analysis_group_by_period: '/mcp/analysis/group_by_period',
  analysis_compare_cities: '/mcp/analysis/compare_cities',
  analysis_extreme_event_stats: '/mcp/analysis/extreme_event_stats',
  analysis_simple_forecast: '/mcp/analysis/simple_forecast',
  'data.get_range': '/mcp/data.get_range',
  'data.get_dataset_overview': '/mcp/data.get_dataset_overview',
  'data.check_coverage': '/mcp/data.check_coverage',
  'data.custom_query': '/mcp/data.custom_query',
  'data.update_city_range': '/mcp/data.update_city_range',
  'analysis.describe_timeseries': '/mcp/analysis/describe_timeseries',
  'analysis.group_by_period': '/mcp/analysis/group_by_period',
  'analysis.compare_cities': '/mcp/analysis/compare_cities',
  'analysis.extreme_event_stats': '/mcp/analysis/extreme_event_stats',
  'analysis.simple_forecast': '/mcp/analysis/simple_forecast',
};

export const listTools = () => api.get('/mcp/tools');

export const callTool = async (toolName, args = {}) => {
  const path = TOOL_ROUTE[toolName] || `/mcp/${toolName}`;
  const { data } = await api.post(path, args);
  return data;
};

export default { listTools, callTool };
