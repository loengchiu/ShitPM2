import { createRoot } from 'react-dom/client';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';
import './styles/global.css';
// 默认且唯一的正式 Prototype 视觉入口：Tabler Token + Ant Design 适配。
import { tablerTheme, tablerCssVars } from './theme/tablerTheme';
import App from './App.jsx';

// CSS 变量注入：顶栏/标签栏/操作栏等壳层硬编码色随主题走
const rootStyle = document.documentElement.style;
Object.entries(tablerCssVars).forEach(([key, value]) => rootStyle.setProperty(key, value));

createRoot(document.getElementById('root')).render(
  <ConfigProvider locale={zhCN} theme={tablerTheme}>
    <AntdApp>
      <App />
    </AntdApp>
  </ConfigProvider>,
);
