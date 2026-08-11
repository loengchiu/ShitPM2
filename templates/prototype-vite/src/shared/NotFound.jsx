import { Button, Result } from 'antd';

export default function NotFound() {
  return (
    <Result
      status="404"
      title="404"
      subTitle="页面不存在"
      extra={
        <Button type="primary" onClick={() => (window.location.hash = '#/')}>
          返回首页
        </Button>
      }
    />
  );
}
