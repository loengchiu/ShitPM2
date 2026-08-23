import { App, Button, Card, Table, Tag, Typography } from 'antd';
import { IconArrowLeft, IconDownload, IconEdit, IconPrinter } from '@tabler/icons-react';
import DetailList from '../../shared/ui/DetailList.jsx';
import PageFooter from '../../shared/ui/PageFooter.jsx';
import { navigate } from '../../shared/useHashRoute.js';

const { Title } = Typography;

const columns = [
  { title: '期数', dataIndex: 'period', key: 'period', width: 90 },
  { title: '应收金额', dataIndex: 'amount', key: 'amount', width: 110, align: 'right' },
  { title: '实收金额', dataIndex: 'paid', key: 'paid', width: 110, align: 'right' },
  { title: '收款日期', dataIndex: 'date', key: 'date', width: 120 },
  { title: '收款方式', dataIndex: 'method', key: 'method', width: 110 },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    render: (v) => <Tag color={v === '已缴清' ? 'success' : 'processing'}>{v}</Tag>,
  },
];

const records = [
  { key: 1, period: '2026-07', amount: '12,800.00', paid: '12,800.00', date: '2026-07-25', method: '银行转账', status: '已缴清' },
  { key: 2, period: '2026-06', amount: '12,800.00', paid: '12,800.00', date: '2026-06-26', method: '银行转账', status: '已缴清' },
  { key: 3, period: '2026-05', amount: '12,800.00', paid: '12,800.00', date: '2026-05-27', method: '对公转账', status: '已缴清' },
  { key: 4, period: '2026-04', amount: '12,800.00', paid: '12,800.00', date: '2026-04-25', method: '银行转账', status: '已缴清' },
];

const baseInfo = [
  { label: '商户名称', value: '肯德基（东区店）' },
  { label: '所属服务区', value: '松山湖服务区' },
  { label: '合同编号', value: 'HT-2026-0032' },
  { label: '租赁面积', value: '180 ㎡' },
  { label: '租赁期限', value: '2026-04-01 ~ 2027-03-31' },
  { label: '月租金', value: '12,800.00 元' },
  { label: '联系人', value: '王经理' },
  { label: '联系电话', value: '138****6621' },
  { label: '入驻日期', value: '2026-04-01' },
  { label: '到期日期', value: '2027-03-31' },
  { label: '商户类型', value: '餐饮' },
  { label: '经营状态', value: <Tag color="processing">正常经营</Tag> },
];

const paymentInfo = [
  { label: '缴费周期', value: '按月' },
  { label: '收款方式', value: '银行转账' },
  { label: '收款账户', value: '交通银行 6222 **** **** 8841' },
  { label: '开票类型', value: '增值税普通发票' },
  { label: '开票抬头', value: '东莞市肯德基餐饮有限公司' },
  { label: '税率', value: '6%' },
  { label: '下次应收日', value: '2026-08-25' },
  { label: '催缴提醒', value: <Tag color="warning">提前 5 天提醒</Tag> },
];

const noteInfo = [
  {
    label: '备注',
    value:
      '该商户为 2026 年 4 月新签约商户，租金按合同约定每月 25 日前缴纳。水电费按实际用量另行结算。',
  },
];

export default function DetailDemo() {
  const { message } = App.useApp();

  return (
    <div>
      {/* 内页显式标题 + 返回按钮（右上角，与标题对齐） */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Title level={4} style={{ margin: 0 }}>商户详情</Title>
        <Button icon={<IconArrowLeft size={16} />} onClick={() => navigate('/')}>返回</Button>
      </div>

      {/* 状态摘要行（信息展示，非按钮） */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <Tag color="success">已缴清</Tag>
        <span style={{ color: '#6c6a64', fontSize: 13 }}>合同编号 HT-2026-0032 · 缴费周期 2026-04 ~ 2027-03</span>
      </div>

      {/* 基本信息：20/30/20/30 */}
      <DetailList title="基本信息" items={baseInfo} variant="pair" />

      {/* 缴费信息：20/30/20/30 */}
      <DetailList title="缴费信息" items={paymentInfo} variant="pair" />

      {/* 收款明细 */}
      <Card className="detail-records-card" size="small" title="收款明细" style={{ marginBottom: 16 }}>
        <Table columns={columns} dataSource={records} pagination={false} size="middle" />
      </Card>

      {/* 备注：20/80 */}
      <DetailList title="备注" items={noteInfo} variant="text" />

      {/* 内页底部版权（内容最底部一行） */}
      <PageFooter />

      {/* 页面级操作栏：底部通栏贴底，靠右 */}
      <div className="page-action-bar">
        <Button icon={<IconEdit size={16} />} onClick={() => navigate('/form-demo?mode=edit&id=1')}>编辑</Button>
        <Button icon={<IconPrinter size={16} />} onClick={() => message.info('打印预览已准备')}>打印</Button>
        <Button type="primary" icon={<IconDownload size={16} />} onClick={() => message.success('账单已导出')}>导出账单</Button>
      </div>
    </div>
  );
}
