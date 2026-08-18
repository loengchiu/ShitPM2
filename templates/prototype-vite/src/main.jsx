import { createRoot } from 'react-dom/client';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';
import './styles/global.css';
import App from './App.jsx';
import tablerTheme from './theme/tablerTheme';
import { tablerCssVariables } from './theme/tablerTokens';

const root = document.getElementById('root');

// 把 Token 同步为 CSS 变量，供 global.css 的补丁样式引用（避免页面级重复声明视觉值）
Object.entries(tablerCssVariables).forEach(([name, value]) => {
  document.documentElement.style.setProperty(name, value);
});

createRoot(root).render(
  <ConfigProvider locale={zhCN} theme={tablerTheme}>
    <AntdApp>
      <App />
    </AntdApp>
  </ConfigProvider>,
);
