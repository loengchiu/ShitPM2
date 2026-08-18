import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';
import './styles/global.css';
import App from './App.jsx';
import tablerTheme from './theme/tablerTheme';
import { tablerCssVariables } from './theme/tablerTokens';

const root = document.getElementById('root');

// 把 Token 同步为 CSS 变量，供 global.css 的补丁样式引用（避免页面级重复声明视觉值）
Object.entries(tablerCssVariables).forEach(([name, value]) => {
  root.style.setProperty(name, value);
});

createRoot(root).render(
  <ConfigProvider locale={zhCN} theme={tablerTheme}>
    <App />
  </ConfigProvider>,
);
