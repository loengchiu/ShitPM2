import { Button, Card, Result } from 'antd';

export default function NotFound() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 64 }}>
      <Card style={{ maxWidth: 720, width: '100%' }}>
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
      </Card>
    </div>
  );
}
