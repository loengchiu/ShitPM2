// Claude 设计语言转译 → antd v6 ConfigProvider 主题
// 来源：getdesign.md/awesome-design-md 的 claude DESIGN.md（暖米色 canvas + 珊瑚橙主色）
// 取舍：保留暖色基底与珊瑚橙强调；标题不用衬线（中后台场景），字体走系统无衬线栈
import type { ThemeConfig } from 'antd';

export const claudeTheme: ThemeConfig = {
  token: {
    // 品牌与强调（coral）
    colorPrimary: '#cc785c',
    colorPrimaryActive: '#a9583e',
    colorPrimaryHover: '#d98f76',
    // 表面（cream，页面底调浅：接近白的微暖）
    colorBgLayout: '#fcfbf9',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    // 文字（warm dark 体系）
    colorText: '#3d3d3a',
    colorTextHeading: '#141413',
    colorTextSecondary: '#6c6a64',
    colorTextTertiary: '#8e8b82',
    colorTextDisabled: '#c0bdb6',
    // 边框（hairline）
    colorBorder: '#e6dfd8',
    colorBorderSecondary: '#ebe6df',
    colorSplit: '#ebe6df',
    // 语义
    colorSuccess: '#5db872',
    colorWarning: '#d4a017',
    colorError: '#c64545',
    colorInfo: '#cc785c',
    colorLink: '#cc785c',
    colorLinkHover: '#d98f76',
    // 尺度
    borderRadius: 8,
    fontSize: 14,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif',
  },
  components: {
    Button: {
      fontWeight: 500,
      controlHeight: 32,
      borderRadius: 8,
    },
    Card: {
      borderRadiusLG: 12,
    },
    Table: {
      headerBg: '#faf8f4', // 表头浅米（比页面底深半档，不再 #f5f0e8 深米）
      headerColor: '#141413',
      rowHoverBg: '#faf6f0',
    },
    Layout: {
      siderBg: '#fcfbf9',
      headerBg: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#f7ede7', // 选中浅珊瑚（同步调浅）
      itemSelectedColor: '#a9583e',
      itemColor: '#6c6a64',
    },
    Tabs: {
      cardBg: '#faf8f4', // 标签卡浅米（同步调浅）
      itemColor: '#6c6a64',
      itemHoverColor: '#a9583e',
      itemSelectedColor: '#a9583e',
    },
  },
};

// CSS 变量：供 global.css / 壳层硬编码引用（顶栏、标签栏、操作栏、系统名等随主题走）
// 值对齐 bc35d84（10:15）时点的壳层硬编码色，保证切换主题后观感一致
export const claudeCssVars: Record<string, string> = {
  '--brand': '#cc785c',
  '--brand-hover': '#d98f76',
  '--brand-active': '#a9583e',
  '--layout-bg': '#fcfbf9', // 页面底调浅：接近白的微暖
  '--card-bg': '#ffffff',
  '--surface-elevated': '#ffffff', // 顶栏/标签栏/操作栏（bc35d84 均为白）
  '--border': '#e6dfd8',
  '--border-soft': '#ebe6df',
  '--text': '#3d3d3a',
  '--text-secondary': '#6c6a64',
  '--text-tertiary': '#8e8b82',
  '--detail-label-bg': '#faf8f4', // label 带浅米（同步调浅）
  '--menu-selected-bg': '#f7ede7', // 浅珊瑚选中（同步调浅）
  '--menu-selected-text': '#a9583e',
  '--avatar-bg': '#cc785c',
};
