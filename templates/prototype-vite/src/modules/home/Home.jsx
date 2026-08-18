import { Button, Col, Row, Space } from 'antd';
import { useMemo, useState } from 'react';
import { IconChartBar, IconEye, IconInbox, IconList, IconPlus, IconRefresh, IconSearch } from '@tabler/icons-react';
import { TablerChart, tablerChartAxis, tablerChartPalette } from '../../shared/charts/TablerChart';
import {
  TablerActionBar,
  TablerDataTable,
  TablerMetricCard,
  TablerSectionCard,
  TablerStatusTag,
  TablerToolbar,
} from '../../shared/ui';

// 模板占位页：展示共享 UI 与 Tabler 视觉的调用方式，生成原型时按 Design 替换
const initialRows = [
  { key: '1', name: '示例任务甲', status: 'progress', owner: '张工', createdAt: '2026-08-17 09:30' },
  { key: '2', name: '示例任务乙', status: 'success', owner: '李工', createdAt: '2026-08-17 10:00' },
  { key: '3', name: '示例任务丙', status: 'warning', owner: '王工', createdAt: '2026-08-17 11:20' },
  { key: '4', name: '示例任务丁', status: 'error', owner: '赵工', createdAt: '2026-08-17 14:05' },
];

export default function Home() {
  const [rows, setRows] = useState(initialRows);
  const [loading, setLoading] = useState(false);
  const chartOption = useMemo(
    () => ({
      color: tablerChartPalette,
      tooltip: { trigger: 'axis' },
      grid: { left: 12, right: 16, top: 24, bottom: 8, containLabel: true },
      xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五'], ...tablerChartAxis },
      yAxis: { type: 'value', ...tablerChartAxis },
      series: [
        {
          name: '示例趋势',
          type: 'line',
          smooth: true,
          data: [12, 18, 15, 26, 24],
          itemStyle: { color: tablerChartPalette[0] },
          lineStyle: { width: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(6,111,209,0.22)' },
                { offset: 1, color: 'rgba(6,111,209,0.02)' },
              ],
            },
          },
        },
      ],
    }),
    [],
  );

  const refresh = () => {
    setLoading(true);
    window.setTimeout(() => setLoading(false), 500);
  };

  const columns = [
    { title: '任务名称', dataIndex: 'name' },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      render: (value) => <TablerStatusTag status={value} />,
    },
    { title: '负责人', dataIndex: 'owner', width: 120 },
    { title: '创建时间', dataIndex: 'createdAt', width: 180 },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space size={0} style={{ whiteSpace: 'nowrap' }}>
          <Button type="link" size="small">查看</Button>
          <Button type="link" size="small">编辑</Button>
          <Button
            type="link"
            size="small"
            danger
            onClick={() => setRows((prev) => prev.filter((item) => item.key !== record.key))}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 不设页面大标题：壳层页签栏表达当前页面；顶部只放操作区 */}
      <div className="page-actions">
        <Space>
          <Button icon={<IconSearch size={16} />}>查询</Button>
          <Button type="primary" icon={<IconPlus size={16} />}>
            新建任务
          </Button>
        </Space>
      </div>

      <section className="dashboard-section dashboard-metrics" aria-label="关键指标">
        <Row gutter={16}>
          <Col xs={12} md={6}>
            <TablerMetricCard title="今日待办" value={12} trend="up" trendLabel="较昨日 +3" icon={<IconList size={16} />} />
          </Col>
          <Col xs={12} md={6}>
            <TablerMetricCard title="本月新增" value={48} suffix="项" trend="down" trendLabel="较上月 -5" icon={<IconChartBar size={16} />} />
          </Col>
          <Col xs={12} md={6}>
            <TablerMetricCard title="已完成" value={36} trend="up" trendLabel="完成率 75%" icon={<IconEye size={16} />} />
          </Col>
          <Col xs={12} md={6}>
            <TablerMetricCard title="异常告警" value="暂无" icon={<IconInbox size={16} />} />
          </Col>
        </Row>
      </section>

      <section className="dashboard-section">
        <TablerSectionCard
          title="近期趋势"
          extra={<span style={{ color: 'var(--spm-color-text-secondary)' }}>最近五日</span>}
        >
          <TablerChart option={chartOption} height={240} />
        </TablerSectionCard>
      </section>

      <section className="dashboard-section">
        <TablerSectionCard title="任务列表">
          <TablerToolbar
            actions={
              <Space>
                <Button size="small" icon={<IconRefresh size={16} />} onClick={refresh}>
                  刷新
                </Button>
                <Button size="small" onClick={() => setRows([])}>
                  清空数据
                </Button>
                <Button size="small" onClick={() => setRows(initialRows)}>
                  恢复数据
                </Button>
              </Space>
            }
          >
            <span style={{ color: 'var(--spm-color-text-secondary)' }}>共 {rows.length} 条任务</span>
          </TablerToolbar>

          <TablerDataTable
            rowKey="key"
            columns={columns}
            dataSource={rows}
            loading={loading}
            emptyTitle="暂无任务"
            emptyDescription="当前条件下没有数据，可调整查询条件后重试"
            pagination={false}
          />
        </TablerSectionCard>
      </section>

      <TablerActionBar>
        <Button icon={<IconRefresh size={16} />}>重置</Button>
        <Button type="primary" icon={<IconPlus size={16} />}>
          保存
        </Button>
      </TablerActionBar>
    </div>
  );
}
