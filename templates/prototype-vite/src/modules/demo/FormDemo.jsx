import { useEffect, useMemo, useState } from 'react';
import { App as AntdApp, Button, Col, Form, Input, Row, Select } from 'antd';
import { IconCheck, IconRefresh, IconX } from '@tabler/icons-react';
import { navigate } from '../../shared/useHashRoute.js';
import {
  TablerActionBar,
  TablerFormSection,
  TablerPageHeader,
} from '../../shared/ui';

const defaultValues = {
  taskName: '',
  owner: undefined,
  priority: undefined,
  description: '',
  creator: '系统管理员',
  createdAt: '2026-08-18 09:30',
};

function getInitialValues(mode, id) {
  if (mode === 'create') return defaultValues;
  return {
    taskName: '示例任务' + (id || '1'),
    owner: 'zhang',
    priority: 'high',
    description: '这是模板示例数据，用于验证编辑态和只读态的回填行为。',
    creator: '系统管理员',
    createdAt: '2026-08-18 09:30',
  };
}

// 模板示例页：展示分区表单与真实校验、回填、提交和页面外操作栏
export default function FormDemo({ query }) {
  const [form] = Form.useForm();
  const { message } = AntdApp.useApp();
  const [submitting, setSubmitting] = useState(false);
  const requestedMode = query?.get('mode') || 'create';
  const mode = ['create', 'edit', 'view'].includes(requestedMode) ? requestedMode : 'create';
  const id = query?.get('id') || '';
  const readOnly = mode === 'view';
  const initialValues = useMemo(() => getInitialValues(mode, id), [mode, id]);

  useEffect(() => {
    setSubmitting(false);
    form.resetFields();
    form.setFieldsValue(initialValues);
  }, [form, initialValues]);

  const onFinish = (values) => {
    setSubmitting(true);
    window.setTimeout(() => {
      setSubmitting(false);
      message.success(mode === 'edit' ? '任务已更新' : '任务已创建');
    }, 400);
  };

  const onFinishFailed = () => {
    message.error('请先完善必填字段');
  };

  return (
    <div>
      <TablerPageHeader
        prefix="示例"
        title={mode === 'view' ? '查看任务' : mode === 'edit' ? '编辑任务' : '新建任务'}
        subtitle={id ? '示例 ID：' + id : '表单页骨架：页头 → 分区 Card → 校验反馈 → 底部 sticky 操作栏'}
      />

      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        disabled={readOnly}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        style={{ maxWidth: 960 }}
      >
        <TablerFormSection title="基本信息">
          <Row gutter={24}>
            <Col span={8} xs={24} md={8}>
              <Form.Item
                label="任务名称"
                name="taskName"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="请输入任务名称" />
              </Form.Item>
            </Col>
            <Col span={8} xs={24} md={8}>
              <Form.Item
                label="负责人"
                name="owner"
                rules={[{ required: true, message: '请选择负责人' }]}
              >
                <Select placeholder="请选择负责人" options={[{ value: 'zhang', label: '张工' }, { value: 'li', label: '李工' }]} />
              </Form.Item>
            </Col>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="优先级" name="priority">
                <Select placeholder="请选择优先级" options={[{ value: 'high', label: '高' }, { value: 'normal', label: '普通' }]} />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="任务描述" name="description">
                <Input.TextArea autoSize={{ minRows: 4, maxRows: 8 }} placeholder="请输入任务描述" />
              </Form.Item>
            </Col>
          </Row>
        </TablerFormSection>

        <TablerFormSection title="系统判定字段">
          <Row gutter={24}>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="创建人" name="creator">
                <Input disabled />
              </Form.Item>
            </Col>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="创建时间" name="createdAt">
                <Input disabled />
              </Form.Item>
            </Col>
          </Row>
        </TablerFormSection>
      </Form>

      <TablerActionBar>
        {readOnly ? (
          <Button icon={<IconX size={16} />} onClick={() => navigate('/')}>
            返回
          </Button>
        ) : (
          <>
            <Button icon={<IconRefresh size={16} />} onClick={() => form.resetFields()}>
              重置
            </Button>
            <Button icon={<IconX size={16} />} onClick={() => navigate('/')}>
              取消
            </Button>
            <Button type="primary" loading={submitting} icon={<IconCheck size={16} />} onClick={() => form.submit()}>
              提交
            </Button>
          </>
        )}
      </TablerActionBar>
    </div>
  );
}
