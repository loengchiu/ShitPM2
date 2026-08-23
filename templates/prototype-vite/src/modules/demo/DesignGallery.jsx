// DesignGallery：设计语言样张页——聚合展示中后台典型元素
// 用途：评审 Claude 主题观感；元素覆盖指标卡/工具栏/表格(钉首末列)/表单/标签/按钮
import { useMemo, useState } from 'react';
import PageFooter from '../../shared/ui/PageFooter.jsx';
import {
  App,
  Badge,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Input,
  Radio,
  Row,
  Select,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd';
import {
  IconDots,
  IconDownload,
  IconEdit,
  IconPlus,
  IconSearch,
  IconTrash,
} from '@tabler/icons-react';

const { Text } = Typography;

const statusColor = { 已缴清: 'success', 待缴: 'processing', 逾期: 'error', 部分缴纳: 'warning' };

function buildColumns({ onEdit, onDelete, onMore }) {
  return [
  { title: '单号', dataIndex: 'no', key: 'no', width: 140, fixed: 'left' },
  { title: '商户', dataIndex: 'shop', key: 'shop', width: 140 },
  { title: '所属服务区', dataIndex: 'area', key: 'area', width: 160 },
  { title: '应收金额', dataIndex: 'amount', key: 'amount', width: 120, align: 'right' },
  { title: '实收金额', dataIndex: 'paid', key: 'paid', width: 120, align: 'right' },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 110,
    render: (v) => <Tag color={statusColor[v]}>{v}</Tag>,
  },
  { title: '收款日期', dataIndex: 'date', key: 'date', width: 120 },
  {
    title: '操作',
    key: 'action',
    width: 160,
    fixed: 'right',
    render: (_, record) => (
      <Space size="small">
        <Button type="link" size="small" icon={<IconEdit size={16} />} onClick={() => onEdit(record)}>
          编辑
        </Button>
        <Button type="link" size="small" danger icon={<IconTrash size={16} />} onClick={() => onDelete(record)}>
          删除
        </Button>
        <Button type="text" size="small" icon={<IconDots size={16} />} aria-label="更多操作" onClick={() => onMore(record)} />
      </Space>
    ),
  },
  ];
}

const data = [
  { key: 1, no: 'ZF20260821001', shop: '肯德基（东区店）', area: '松山湖服务区', amount: 12800, paid: 12800, status: '已缴清', date: '2026-08-20' },
  { key: 2, no: 'ZF20260821002', shop: '美宜佳便利店', area: '松山湖服务区', amount: 8600, paid: 8600, status: '已缴清', date: '2026-08-20' },
  { key: 3, no: 'ZF20260821003', shop: '粤运加油站', area: '大岭山服务区', amount: 45200, paid: 30000, status: '部分缴纳', date: '2026-08-19' },
  { key: 4, no: 'ZF20260821004', shop: '瑞幸咖啡', area: '大岭山服务区', amount: 7200, paid: 0, status: '待缴', date: '-' },
  { key: 5, no: 'ZF20260821005', shop: '永和大王', area: '虎门服务区', amount: 15600, paid: 0, status: '逾期', date: '-' },
  { key: 6, no: 'ZF20260821006', shop: '喜茶', area: '虎门服务区', amount: 9800, paid: 9800, status: '已缴清', date: '2026-08-18' },
];

export default function DesignGallery() {
  const [form, setForm] = useState({ area: undefined, status: undefined, keyword: '' });
  const [rows, setRows] = useState(data);
  const { message } = App.useApp();
  const columns = useMemo(
    () => buildColumns({
      onEdit: (record) => message.info('正在编辑 ' + record.no),
      onDelete: (record) => {
        setRows((current) => current.filter((item) => item.key !== record.key));
        message.success('已删除 ' + record.no);
      },
      onMore: (record) => message.info(record.no + ' 暂无更多操作'),
    }),
    [message],
  );
  const resetFilters = () => setForm({ area: undefined, status: undefined, keyword: '' });
  return (
    <div>
      {/* 页面操作行（页面级操作按钮统一在底部 page-action-bar） */}

      {/* 指标卡 */}
      <Row gutter={[16, 16]}>
        {[
          { title: '本月应收', value: 286400, suffix: '元' },
          { title: '本月实收', value: 251800, suffix: '元' },
          { title: '收缴率', value: 87.9, suffix: '%' },
          { title: '逾期未缴', value: 12, suffix: '笔' },
        ].map((it) => (
          <Col xs={12} md={6} key={it.title}>
            <Card size="small">
              <Statistic title={it.title} value={it.value} suffix={it.suffix} precision={it.suffix === '%' ? 1 : 0} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 工具栏 */}
      <Card size="small" style={{ marginTop: 16 }}>
        <Space wrap>
          <Input
            placeholder="搜索单号 / 商户"
            prefix={<IconSearch size={16} style={{ color: '#8e8b82' }} />}
            style={{ width: 220 }}
            value={form.keyword}
            onChange={(e) => setForm({ ...form, keyword: e.target.value })}
          />
          <Select
            placeholder="所属服务区"
            style={{ width: 160 }}
            allowClear
            value={form.area}
            onChange={(area) => setForm({ ...form, area })}
            options={['松山湖服务区', '大岭山服务区', '虎门服务区'].map((v) => ({ value: v, label: v }))}
          />
          <Select
            placeholder="状态"
            style={{ width: 120 }}
            allowClear
            value={form.status}
            onChange={(status) => setForm({ ...form, status })}
            options={['已缴清', '待缴', '部分缴纳', '逾期'].map((v) => ({ value: v, label: v }))}
          />
          <DatePicker.RangePicker placeholder={['开始日期', '结束日期']} />
          <Button type="primary" onClick={() => message.success('已按当前条件查询')}>查询</Button>
          <Button onClick={resetFilters}>重置</Button>
        </Space>
      </Card>

      {/* 表格：首列 + 末列固定 */}
      <Card size="small" style={{ marginTop: 16 }} title="收款明细（首列与操作列固定）">
        <Table columns={columns} dataSource={rows} scroll={{ x: 1400 }} pagination={{ pageSize: 5, showTotal: (t) => `共 ${t} 条` }} size="middle" />
      </Card>

      {/* 表单分组 */}
      <Card size="small" style={{ marginTop: 16 }} title="表单控件">
        <Row gutter={[24, 16]}>
          <Col xs={24} md={12}>
            <Space orientation="vertical" style={{ width: '100%' }} size="middle">
              <div><Text>商户名称</Text><Input placeholder="请输入商户名称" style={{ marginTop: 4 }} /></div>
              <div><Text>收费项目</Text><Select style={{ width: '100%', marginTop: 4 }} placeholder="请选择收费项目" options={['场地租金', '物业管理费', '水电费', '广告位费'].map((v) => ({ value: v, label: v }))} /></div>
              <div><Text>收款日期</Text><DatePicker.RangePicker style={{ width: '100%', marginTop: 4 }} /></div>
              <div>
                <Text>计费方式</Text>
                <Radio.Group style={{ marginTop: 4 }} defaultValue="monthly">
                  <Radio value="monthly">按月</Radio>
                  <Radio value="quarterly">按季</Radio>
                  <Radio value="yearly">按年</Radio>
                </Radio.Group>
              </div>
              <div>
                <Text>收费项目（多选）</Text>
                <Checkbox.Group style={{ marginTop: 4 }} options={['场地租金', '物业管理费', '水电费']} defaultValue={['场地租金']} />
              </div>
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space orientation="vertical" style={{ width: '100%' }} size="middle">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>自动催缴提醒</Text>
                <Switch defaultChecked />
              </div>
              <div><Text>备注</Text><Input.TextArea rows={3} placeholder="补充说明" style={{ marginTop: 4 }} /></div>
              <div>
                <Text>操作按钮</Text>
                <div style={{ marginTop: 8 }}>
                  <Space wrap>
                    <Button type="primary" onClick={() => message.success('已执行主操作')}>主操作</Button>
                    <Button onClick={() => message.info('已执行次操作')}>次操作</Button>
                    <Button type="dashed" onClick={() => message.info('已执行虚线操作')}>虚线</Button>
                    <Button type="text" onClick={() => message.info('已执行文本操作')}>文本按钮</Button>
                    <Button type="link" onClick={() => message.info('已执行链接操作')}>链接按钮</Button>
                    <Button danger onClick={() => message.warning('危险操作仅作样张反馈')}>危险操作</Button>
                    <Button type="primary" loading>加载中</Button>
                    <Button disabled>禁用</Button>
                  </Space>
                </div>
              </div>
              <div>
                <Text>状态标签</Text>
                <div style={{ marginTop: 8 }}>
                  <Space wrap>
                    <Tag color="success">已缴清</Tag>
                    <Tag color="processing">处理中</Tag>
                    <Tag color="warning">待确认</Tag>
                    <Tag color="error">已逾期</Tag>
                    <Tag>默认</Tag>
                    <Badge status="success" text="运行正常" />
                    <Badge status="warning" text="即将到期" />
                    <Badge status="error" text="已欠费" />
                  </Space>
                </div>
              </div>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 内页底部版权（内容最底部一行） */}
      <PageFooter />

      {/* 页面级操作栏：底部，靠右 */}
      <div className="page-action-bar">
        <Button icon={<IconDownload size={16} />} onClick={() => message.success('收款明细已导出')}>导出</Button>
        <Button type="primary" icon={<IconPlus size={16} />} onClick={() => message.success('新增收款单表单已准备')}>新增收款单</Button>
      </div>
    </div>
  );
}
