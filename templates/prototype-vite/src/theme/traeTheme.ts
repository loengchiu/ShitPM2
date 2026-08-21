// Trae 设计语言转译 → antd v6 ConfigProvider 主题
// 来源：TraeWork 设计系统（references/design-sources/traework/，字节 AI IDE 设计语言）
// 特征：中性灰底 + 靛蓝科技强调（冷色调），圆角偏方（IDE 工具风）
import type { ThemeConfig } from 'antd';

export const traeTheme: ThemeConfig = {
  token: {
    // 品牌与强调（靛蓝）
    colorPrimary: '#4B3FE3',
    colorPrimaryActive: '#3F31C6',
    colorPrimaryHover: '#6A6FFF',
    // 表面（中性灰，冷色调）
    colorBgLayout: '#F5F5F5',
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#FFFFFF',
    // 文字（近黑灰体系）
    colorText: '#171717',
    colorTextHeading: '#171717',
    colorTextSecondary: '#404040',
    colorTextTertiary: '#737373',
    colorTextDisabled: '#A1A1A1',
    // 边框
    colorBorder: '#E5E5E5',
    colorBorderSecondary: '#F0F0F0',
    colorSplit: '#F0F0F0',
    // 语义（Trae status 体系）
    colorSuccess: '#15A877',
    colorWarning: '#E27900',
    colorError: '#E8463A',
    colorInfo: '#2F74FF',
    colorLink: '#4B3FE3',
    colorLinkHover: '#6A6FFF',
    // 尺度（IDE 风偏方：控件 6、卡片 12）
    borderRadius: 6,
    fontSize: 14,
    fontFamily:
      '"SF Pro Text", "PingFang SC", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  },
  components: {
    Button: {
      fontWeight: 500,
      controlHeight: 32,
      borderRadius: 6,
    },
    Card: {
      borderRadiusLG: 12,
    },
    Table: {
      headerBg: '#F5F5F5',
      headerColor: '#171717',
      rowHoverBg: '#FAFAFA',
    },
    Layout: {
      siderBg: '#FFFFFF',
      headerBg: '#FFFFFF',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#EEEEFB',
      itemSelectedColor: '#4B3FE3',
      itemColor: '#404040',
    },
    Tabs: {
      cardBg: '#F5F5F5',
      itemColor: '#404040',
      itemHoverColor: '#4B3FE3',
      itemSelectedColor: '#4B3FE3',
    },
  },
};

// CSS 变量：供 global.css / 壳层硬编码引用（随主题走）
export const traeCssVars: Record<string, string> = {
  '--brand': '#4B3FE3',
  '--brand-hover': '#6A6FFF',
  '--brand-active': '#3F31C6',
  '--layout-bg': '#F5F5F5',
  '--card-bg': '#FFFFFF',
  '--surface-elevated': '#FFFFFF',
  '--border': '#E5E5E5',
  '--border-soft': '#F0F0F0',
  '--text': '#171717',
  '--text-secondary': '#404040',
  '--text-tertiary': '#737373',
  '--detail-label-bg': '#F5F5F5',
  '--menu-selected-bg': '#EEEEFB',
  '--menu-selected-text': '#4B3FE3',
  '--avatar-bg': '#4B3FE3',
};
