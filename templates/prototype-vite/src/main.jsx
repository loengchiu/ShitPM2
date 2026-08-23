import { createRoot } from 'react-dom/client';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';
import './styles/global.css';
// 主题接入点：换设计语言时改这两行（主题文件在 src/theme/，流程见 references/prototype-writing.md「品牌主题接入」）
// 默认主题 = Tabler（2026-08-21 用户拍板）；要 Claude 时改回 claudeTheme/claudeCssVars
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
