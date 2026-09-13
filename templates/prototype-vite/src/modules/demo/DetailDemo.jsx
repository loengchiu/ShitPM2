import { App, Button } from 'antd';
import { IconDownload, IconEdit, IconPrinter } from '../../shared/icons';
import {
  ActionBar,
  DataTable,
  PageFooter,
  PageHeader,
  SectionCard,
  StatusTag,
} from '../../shared/ui';
import DetailList from '../../shared/ui/DetailList.jsx';
import { navigate } from '../../shared/useHashRoute.js';
import { useRole } from '../../shared/role.jsx';

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
    render: (v) => <StatusTag status={v === '已缴清' ? 'success' : 'progress'} text={v} />,
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
  { label: '补充协议', value: null }, // 空字段示例：由 DetailList 自动展示为 —
  { label: '经营状态', value: <StatusTag status="progress" text="正常经营" /> },
];

const paymentInfo = [
  { label: '缴费周期', value: '按月' },
  { label: '收款方式', value: '银行转账' },
  { label: '收款账户', value: '交通银行 6222 **** **** 8841' },
  { label: '开票类型', value: '增值税普通发票' },
  { label: '开票抬头', value: '东莞市肯德基餐饮有限公司' },
  { label: '税率', value: '6%' },
  { label: '下次应收日', value: '2026-08-25' },
  { label: '催缴提醒', value: <StatusTag status="warning" text="提前 5 天提醒" /> },
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
  // 角色差异演示（§2.3）：一线操作员无编辑权限 → 按钮不渲染（不置灰）；
  // 联系人字段对一线不可见 → 整个 label:value 对不渲染（§2.3 字段可见层级）
  const role = useRole();
  const canEdit = role.key !== 'operator';
  const visibleBaseInfo = canEdit
    ? baseInfo
    : baseInfo.filter((it) => !['联系人', '联系电话'].includes(it.label));

  return (
    <div data-page="商户详情">
      {/* 共享 PageHeader + onBack */}
      <PageHeader
        title="商户详情"
        subtitle="合同编号 HT-2026-0032 · 缴费周期 2026-04 ~ 2027-03"
        onBack={() => navigate('/')}
        actions={<StatusTag data-state="已缴清" status="success" text="已缴清" />}
      />

      {/* 基本信息：20/30/20/30（一线角色不渲染联系人字段对；空字段展示为 —） */}
      <div data-block="基本信息"><DetailList title="基本信息" items={visibleBaseInfo} variant="pair" /></div>

      {/* 缴费信息：20/30/20/30 */}
      <div data-block="缴费信息"><DetailList title="缴费信息" items={paymentInfo} variant="pair" /></div>

      {/* 收款明细 */}
      <SectionCard data-block="收款明细" title="收款明细" style={{ marginBottom: 16 }}>
        <DataTable columns={columns} dataSource={records} pagination={false} />
      </SectionCard>

      {/* 备注：20/80 */}
      <div data-block="备注"><DetailList title="备注" items={noteInfo} variant="text" /></div>

      {/* 内页底部版权（内容最底部一行，在 ActionBar 之前） */}
      <PageFooter />

      {/* 页面级操作栏：共享 ActionBar 贴底 */}
      <ActionBar data-block="页面操作">
        {canEdit && (
          <Button data-operation="编辑" icon={<IconEdit size={16} />} onClick={() => navigate('/form-demo?mode=edit&id=1')}>
            编辑
          </Button>
        )}
        <Button data-operation="打印" icon={<IconPrinter size={16} />} onClick={() => message.info('打印预览已准备')}>
          打印
        </Button>
        <Button data-operation="导出账单" type="primary" icon={<IconDownload size={16} />} onClick={() => message.success('账单已导出')}>
          导出账单
        </Button>
      </ActionBar>
    </div>
  );
}
