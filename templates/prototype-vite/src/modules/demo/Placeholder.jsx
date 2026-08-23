import { Card, Empty } from 'antd';

// 占位页：演示多模块/多子页结构时使用；生成业务原型时替换为真实页面
export default function Placeholder({ placeholder }) {
  return (
    <Card>
      <Empty description={placeholder || '占位页面'} />
    </Card>
  );
}
