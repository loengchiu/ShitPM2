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
    // 表面（cream）
    colorBgLayout: '#faf9f5',
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
      headerBg: '#f5f0e8',
      headerColor: '#141413',
      rowHoverBg: '#faf6f0',
    },
    Layout: {
      siderBg: '#faf9f5',
      headerBg: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#f0e3da',
      itemSelectedColor: '#a9583e',
      itemColor: '#6c6a64',
    },
    Tabs: {
      cardBg: '#f5f0e8',
      itemColor: '#6c6a64',
      itemHoverColor: '#a9583e',
      itemSelectedColor: '#a9583e',
    },
  },
};
