import * as echarts from 'echarts';
import { useEffect, useRef } from 'react';
import { tablerTokens } from '../../theme/tablerTokens';

const { chart } = tablerTokens;

// Tabler 图表视觉适配：色板、坐标轴与网格只在这里定义，页面 option 引用这些值
export const tablerChartPalette = chart.colors;

export const tablerChartAxis = {
  axisLine: { lineStyle: { color: chart.axis } },
  axisTick: { show: false },
  axisLabel: { color: chart.label, fontSize: 12 },
  splitLine: { lineStyle: { color: chart.grid, width: 1 } },
};

/**
 * 统一图表容器：option 必须用 useMemo 保持引用稳定，避免重复 init/dispose。
 * option.color 请使用 tablerChartPalette；坐标轴使用 tablerChartAxis。
 */
export function TablerChart({ option, height = 260, className }) {
  const ref = useRef(null);

  useEffect(() => {
    const chartInstance = echarts.init(ref.current);
    chartInstance.setOption(option);
    const onResize = () => chartInstance.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chartInstance.dispose();
    };
  }, [option]);

  return <div ref={ref} role="img" aria-label="图表" className={className} style={{ width: '100%', height }} />;
}
