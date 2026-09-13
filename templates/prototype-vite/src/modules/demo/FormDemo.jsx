import { App, Button, Card, Col, DatePicker, Form, Input, InputNumber, Radio, Row, Select, Steps } from 'antd';
import { IconRefresh, IconSend, IconX } from '../../shared/icons';
import {
  ActionBar,
  FormSection,
  PageFooter,
  PageHeader,
} from '../../shared/ui';
import { navigate } from '../../shared/useHashRoute.js';

// 表单页样张：内页（由列表页"申请出库"进入）
// 体现：PageHeader + onBack + Steps 审批流 + FormSection + 文本域单独一行 + ActionBar 底部操作栏
export default function FormDemo() {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const submit = async () => {
    try {
      const values = await form.validateFields();
      message.success('出库申请已提交：' + JSON.stringify(values));
    } catch {
      message.error('表单校验失败，请补全必填信息');
    }
  };

  return (
    <div data-page="出库申请">
      {/* 共享 PageHeader + onBack */}
      <PageHeader
        title="出库申请"
        subtitle="填写资产出库申请信息并提交审批"
        onBack={() => navigate('/')}
      />

      {/* 审批流 */}
      <Card data-block="审批流" style={{ marginBottom: 16 }}>
        <Steps
          current={0}
          items={[{ title: '服务区发起' }, { title: '服务区确认' }, { title: '结束' }]}
        />
      </Card>

      {/* 表单：FormSection 承载分区 */}
      <FormSection data-block="出库信息" title="出库信息" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{ type: 'normal' }}
        >
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item label="资产类别" name="category" rules={[{ required: true, message: '请选择资产类别' }]}>
                <Select data-field="资产类别" placeholder="请选择资产类别" options={['固定资产', '低值易耗品', '办公用品'].map((v) => ({ value: v, label: v }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="出库数量" name="qty" rules={[{ required: true, message: '请输入出库数量' }]}>
                <InputNumber data-field="出库数量" style={{ width: '100%' }} min={1} placeholder="请输入数量" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="使用部门" name="dept" rules={[{ required: true, message: '请选择使用部门' }]}>
                <Select data-field="使用部门" placeholder="请选择使用部门" options={['综合管理部', '物业管理部', '工程维修部', '安全保卫部'].map((v) => ({ value: v, label: v }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="期望出库日期" name="date" rules={[{ required: true, message: '请选择日期' }]}>
                <DatePicker data-field="期望出库日期" style={{ width: '100%' }} placeholder="请选择日期" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="出库类型" name="type">
                <Radio.Group data-field="出库类型">
                  <Radio value="normal">正常出库</Radio>
                  <Radio value="borrow">借用</Radio>
                  <Radio value="transfer">调拨</Radio>
                </Radio.Group>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="经办人" name="person" rules={[{ required: true, message: '请输入经办人' }]}>
                <Input data-field="经办人" placeholder="请输入经办人" />
              </Form.Item>
            </Col>
            {/* 文本域：单独一行 */}
            <Col span={24}>
              <Form.Item label="出库原因" name="reason" rules={[{ required: true, message: '请填写出库原因' }]}>
                <Input.TextArea data-field="出库原因" rows={3} placeholder="请填写出库原因，包括用途、使用场景等说明" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="备注" name="remark">
                <Input.TextArea data-field="备注" rows={2} placeholder="其他补充说明（选填）" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </FormSection>

      {/* 内页底部版权（内容最底部一行，在 ActionBar 之前） */}
      <PageFooter />

      {/* 页面级操作栏：ActionBar sticky 贴底，通过 form 实例操作 */}
      <ActionBar data-block="页面操作">
        <Button data-operation="重置" icon={<IconRefresh size={16} />} onClick={() => form.resetFields()}>
          重置
        </Button>
        <Button data-operation="取消" icon={<IconX size={16} />} onClick={() => navigate('/')}>
          取消
        </Button>
        <Button data-operation="提交申请" type="primary" icon={<IconSend size={16} />} onClick={submit}>
          提交申请
        </Button>
      </ActionBar>
    </div>
  );
}
