import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';
import './styles/global.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <ConfigProvider locale={zhCN}>
    <App />
  </ConfigProvider>,
);
