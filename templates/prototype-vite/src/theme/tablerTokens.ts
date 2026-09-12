// 图表色板与坐标轴数值（供 src/shared/charts/TablerChart.jsx 读取）
// 来源：Tabler 官方配色体系，chart.label 与 Tabler 次要文字 gray-500 #6b7280 保持一致
export const tablerTokens = {
  chart: {
    colors: ['#066fd1', '#2fb344', '#f59f00', '#d63939', '#4299e1', '#6f42c1'],
    axis: '#e5e7eb',
    label: '#6b7280',
    grid: '#eef0f2',
  },
} as const;

export default tablerTokens;
