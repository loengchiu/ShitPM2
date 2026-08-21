// Claude 设计语言转译 → antd v6 ConfigProvider 主题
// 来源：Trae 导出的 Claude-2 设计系统（"Claude Copy Copy" 导出目录）
// 取舍：保留暖色基底 + 深陶土强调 + 大圆角 + 卡片暖米（色调分离）；标题不用衬线（中后台场景），字体走系统无衬线栈
import type { ThemeConfig } from 'antd';

export const claudeTheme: ThemeConfig = {
  token: {
    // 品牌与强调（深陶土 terra-cotta，对齐 Trae brand-500/600/400）
    colorPrimary: '#c96442',
    colorPrimaryActive: '#b0562f',
    colorPrimaryHover: '#d6866a',
    // 表面（暖米，色调分离为主，不靠白+边框）
    colorBgLayout: '#faf9f5',
    colorBgContainer: '#f5f4ef', // 卡片暖米（Trae card=bg-200）
    colorBgElevated: '#ffffff', // 浮层/弹层白
    // 文字（warm dark，对齐 Trae text-800/#3d3929）
    colorText: '#3d3929',
    colorTextHeading: '#3d3929',
    colorTextSecondary: '#6e6d68',
    colorTextTertiary: '#908e84',
    colorTextDisabled: '#c2c0b6',
    // 边框（Trae border-300/#dad9d4，对比稍强）
    colorBorder: '#dad9d4',
    colorBorderSecondary: '#e3e0d4',
    colorSplit: '#e3e0d4',
    // 语义（success 保留业务鲜绿；error 对齐 Trae #d64545）
    colorSuccess: '#5db872',
    colorWarning: '#d4a017',
    colorError: '#d64545',
    colorInfo: '#c96442',
    colorLink: '#c96442',
    colorLinkHover: '#d6866a',
    // 尺度（控件圆角 10 防胶囊化——antd 控件高 32px，16px 会成胶囊；
    // 圆滑感由卡片 16px 承担，见 components.Card）
    borderRadius: 10,
    fontSize: 14,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif',
  },
  components: {
    Button: {
      fontWeight: 500,
      controlHeight: 32,
      borderRadius: 10,
    },
    Card: {
      borderRadiusLG: 16, // 卡片大圆角（圆滑感来源）
    },
    Table: {
      headerBg: '#e9e6dc', // 柔米（Trae secondary）
      headerColor: '#3d3929',
      rowHoverBg: '#f0ece2', // 暖米浅一档
    },
    Layout: {
      siderBg: '#faf9f5',
      headerBg: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#f0e3da',
      itemSelectedColor: '#b0562f',
      itemColor: '#6e6d68',
    },
    Tabs: {
      cardBg: '#e9e6dc',
      itemColor: '#6e6d68',
      itemHoverColor: '#b0562f',
      itemSelectedColor: '#b0562f',
    },
  },
};
