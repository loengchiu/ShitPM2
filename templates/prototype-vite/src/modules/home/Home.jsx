import { Card, Typography } from 'antd';

// 模板占位页：生成原型时按 Design 替换为业务首页，并在 routes.jsx 注册全部页面
export default function Home() {
  return (
    <Card>
      <Typography.Title level={4}>{'原型工程已就绪'}</Typography.Title>
      <Typography.Paragraph type="secondary">
        {'在 src/modules/ 下创建业务页面，并注册到 src/routes.jsx。'}
      </Typography.Paragraph>
    </Card>
  );
}
