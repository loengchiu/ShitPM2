// Claude 官方设计语言转译 → antd v6 ConfigProvider 主题
// 来源：D:\LiangchaosBook\Downloads\DESIGN-claude(1).md（Claude.com 官方设计系统）
// 映射原则：每个 antd token 优先取官方 token 语义最近的色值，不造新色。
// 官方无定义处（antd 必需而官方没有）的取舍：
//  - hover：官方不定义 hover（"primary darkens on press; nothing else changes"）→ 直接用 primary-active #a9583e
//  - 容器/浮层白 #ffffff：官方最浅是 canvas #faf9f5（无白色 token）；中后台白容器是用户 2026-08-21 实机拍板过的例外（bc35d84）
//  - disabled 文字：官方无 → 用 muted-soft #8e8b82
import type { ThemeConfig } from 'antd';

export const claudeTheme: ThemeConfig = {
  token: {
    // Brand（官方：primary / primary-active）
    colorPrimary: '#cc785c', // primary coral
    colorPrimaryActive: '#a9583e', // primary-active（按压态）
    colorPrimaryHover: '#a9583e', // 官方无 hover，按压即深
    // Surface（官方：canvas 页面底 / surface-card 内容卡 / surface-soft 软带）
    colorBgLayout: '#faf9f5', // canvas：默认页面底
    colorBgContainer: '#ffffff', // 白容器（用户拍板例外，官方无白色 token）
    colorBgElevated: '#ffffff', // 浮层白（同上例外）
    // Text（官方：ink / body / muted / muted-soft）
    colorText: '#3d3d3a', // body
    colorTextHeading: '#141413', // ink
    colorTextSecondary: '#6c6a64', // muted
    colorTextTertiary: '#8e8b82', // muted-soft
    colorTextDisabled: '#8e8b82', // 官方无 disabled → muted-soft
    // Border（官方：hairline / hairline-soft）
    colorBorder: '#e6dfd8', // hairline：1px 边框
    colorBorderSecondary: '#ebe6df', // hairline-soft
    colorSplit: '#ebe6df', // hairline-soft
    // Semantic（官方：success / warning / error）
    colorSuccess: '#5db872',
    colorWarning: '#d4a017',
    colorError: '#c64545',
    colorInfo: '#cc785c',
    colorLink: '#cc785c',
    colorLinkHover: '#a9583e',
    // 尺度（官方：rounded.md 8px 控件 / rounded.lg 12px 卡片）
    borderRadius: 8,
    fontSize: 14,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif',
  },
  components: {
    Button: {
      fontWeight: 500,
      controlHeight: 32,
      borderRadius: 8, // rounded.md
    },
    Card: {
      borderRadiusLG: 12, // rounded.lg
    },
    Table: {
      headerBg: '#f5f0e8', // surface-soft：软带背景
      headerColor: '#141413', // ink
      rowHoverBg: '#f5f0e8', // surface-soft
    },
    Layout: {
      siderBg: '#faf9f5', // canvas
      headerBg: '#ffffff', // 白顶栏（用户拍板例外；官方 top-nav=canvas）
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#efe9de', // surface-card（官方 category-tab-active 语义）
      itemSelectedColor: '#141413', // ink
      itemColor: '#6c6a64', // muted
    },
    Tabs: {
      cardBg: '#f5f0e8', // surface-soft
      itemColor: '#6c6a64', // muted
      itemHoverColor: '#a9583e',
      itemSelectedColor: '#a9583e',
    },
    Descriptions: {
      labelBg: '#f5f0e8', // surface-soft：详情 label 列与表头统一（antd v6 用 labelBg token，默认 #fafafa 会被覆盖）
    },
  },
};

// CSS 变量：供 global.css / 壳层硬编码引用（顶栏、标签栏、操作栏、系统名等随主题走）
// 全部对齐官方 token；白容器/顶栏为用户拍板例外
export const claudeCssVars: Record<string, string> = {
  '--brand': '#cc785c', // primary
  '--brand-hover': '#a9583e', // primary-active（官方无 hover）
  '--brand-active': '#a9583e', // primary-active
  '--layout-bg': '#faf9f5', // canvas
  '--card-bg': '#ffffff', // 白容器（用户拍板例外）
  '--surface-elevated': '#ffffff', // 顶栏/标签栏/操作栏（用户拍板例外）
  '--border': '#e6dfd8', // hairline
  '--border-soft': '#ebe6df', // hairline-soft
  '--text': '#3d3d3a', // body
  '--text-secondary': '#6c6a64', // muted
  '--text-tertiary': '#8e8b82', // muted-soft
  '--detail-label-bg': '#f5f0e8', // surface-soft（与表头统一）
  '--menu-selected-bg': '#efe9de', // surface-card（category-tab-active）
  '--menu-selected-text': '#141413', // ink
  '--avatar-bg': '#cc785c', // primary
};
