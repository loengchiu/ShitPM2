import { App, Button, Card, Col, DatePicker, Form, Input, InputNumber, Radio, Row, Select, Steps, Typography } from 'antd';
import { IconArrowLeft, IconRefresh, IconSend, IconX } from '@tabler/icons-react';
import PageFooter from '../../shared/ui/PageFooter.jsx';
import { navigate } from '../../shared/useHashRoute.js';

const { Title } = Typography;

// 表单页样张：内页（由列表页"申请出库"进入）
// 体现：显式标题 + 右上返回 + Steps 审批流 + 文本域单独一行 + 底部操作栏（保存/提交/重置/取消为纯文字无图标）
export default function FormDemo() {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const submit = async () => {
    try {
      await form.validateFields();
      message.success('出库申请已提交');
    } catch {
      message.error('请先补全必填信息');
    }
  };
  return (
    <div>
      {/* 内页显式标题 + 返回按钮（右上角） */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Title level={4} style={{ margin: 0 }}>出库申请</Title>
        <Button icon={<IconArrowLeft size={16} />} onClick={() => navigate('/')}>返回</Button>
      </div>

      {/* 审批流 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Steps
          size="small"
          current={0}
          items={[{ title: '服务区发起' }, { title: '服务区确认' }, { title: '结束' }]}
        />
      </Card>

      {/* 表单：普通字段一行两列，文本域单独一行 */}
      <Card size="small" title="出库信息" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{ type: 'normal' }}
        >
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item label="资产类别" name="category" rules={[{ required: true, message: '请选择资产类别' }]}>
                <Select placeholder="请选择资产类别" options={['固定资产', '低值易耗品', '办公用品'].map((v) => ({ value: v, label: v }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="出库数量" name="qty" rules={[{ required: true, message: '请输入出库数量' }]}>
                <InputNumber style={{ width: '100%' }} min={1} placeholder="请输入数量" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="使用部门" name="dept" rules={[{ required: true, message: '请选择使用部门' }]}>
                <Select placeholder="请选择使用部门" options={['综合管理部', '物业管理部', '工程维修部', '安全保卫部'].map((v) => ({ value: v, label: v }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="期望出库日期" name="date" rules={[{ required: true, message: '请选择日期' }]}>
                <DatePicker style={{ width: '100%' }} placeholder="请选择日期" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="出库类型" name="type">
                <Radio.Group>
                  <Radio value="normal">正常出库</Radio>
                  <Radio value="borrow">借用</Radio>
                  <Radio value="transfer">调拨</Radio>
                </Radio.Group>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="经办人" name="person" rules={[{ required: true, message: '请输入经办人' }]}>
                <Input placeholder="请输入经办人" />
              </Form.Item>
            </Col>
            {/* 文本域：单独一行 */}
            <Col span={24}>
              <Form.Item label="出库原因" name="reason" rules={[{ required: true, message: '请填写出库原因' }]}>
                <Input.TextArea rows={3} placeholder="请填写出库原因，包括用途、使用场景等说明" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="备注" name="remark">
                <Input.TextArea rows={2} placeholder="其他补充说明（选填）" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {/* 内页底部版权（内容最底部一行） */}
      <PageFooter />

      {/* 页面级操作栏：底部通栏贴底，按钮带图标 */}
      <div className="page-action-bar">
        <Button icon={<IconRefresh size={16} />} onClick={() => form.resetFields()}>重置</Button>
        <Button icon={<IconX size={16} />} onClick={() => navigate('/')}>取消</Button>
        <Button type="primary" icon={<IconSend size={16} />} onClick={submit}>提交申请</Button>
      </div>
    </div>
  );
}
