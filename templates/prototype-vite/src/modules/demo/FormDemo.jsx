import { Button, Col, Form, Input, Row, Select } from 'antd';
import { IconCheck, IconRefresh, IconX } from '@tabler/icons-react';
import {
  TablerActionBar,
  TablerFormSection,
  TablerPageHeader,
} from '../../shared/ui';

// 模板示例页：展示分区表单与必填/只读/禁用状态的表达方式，生成原型时按 Design 替换
export default function FormDemo() {
  return (
    <div>
      <TablerPageHeader
        prefix="示例"
        title="任务登记"
        subtitle="表单页骨架：页头 → 分区 Card → 校验反馈 → 底部 sticky 操作栏"
      />

      <Form layout="vertical" style={{ maxWidth: 960 }}>
        <TablerFormSection title="基本信息">
          <Row gutter={24}>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="任务名称" required>
                <Input placeholder="请输入任务名称" />
              </Form.Item>
            </Col>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="负责人" required>
                <Select placeholder="请选择负责人" options={[{ value: 'zhang', label: '张工' }]} />
              </Form.Item>
            </Col>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="优先级">
                <Select placeholder="请选择优先级" options={[{ value: 'high', label: '高' }]} />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="任务描述">
                <Input.TextArea autoSize={{ minRows: 4, maxRows: 8 }} placeholder="请输入任务描述" />
              </Form.Item>
            </Col>
          </Row>
        </TablerFormSection>

        <TablerFormSection title="系统判定字段">
          <Row gutter={24}>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="创建人">
                <Input value="系统管理员" disabled />
              </Form.Item>
            </Col>
            <Col span={8} xs={24} md={8}>
              <Form.Item label="创建时间">
                <Input value="2026-08-17 09:30" disabled />
              </Form.Item>
            </Col>
          </Row>
        </TablerFormSection>
      </Form>

      <TablerActionBar>
        <Button icon={<IconRefresh size={16} />}>重置</Button>
        <Button icon={<IconX size={16} />}>取消</Button>
        <Button type="primary" loading icon={<IconCheck size={16} />}>
          提交
        </Button>
      </TablerActionBar>
    </div>
  );
}
