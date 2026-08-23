// Tabler 官方设计语言转译 → antd v6 ConfigProvider 主题
// 来源：Tabler 官方 CSS（preview.tabler.io/dist/css/tabler.min.css，--tblr-* 变量直接解引用）
//       关键值全部来自官方 CSS 定义（2026-08-21 逐元素实测 layout-vertical-transparent/form-layout 页面）：
//   --tblr-primary #066fd1 / --tblr-primary-darken rgb(5.4,99.9,188.1)≈#0563BC（按钮 hover/active）
//   --tblr-shadow-input 0 1px 1px rgba(var(--tblr-body-color-rgb),.06)（输入框+按钮阴影）
//   --tblr-shadow-card 0 0 4px rgba(var(--tblr-body-color-rgb),.04)（卡片阴影）
//   --tblr-shadow-dropdown 0 16px 24px 2px rgba(0,0,0,.07),0 6px 30px 5px rgba(0,0,0,.06),0 8px 10px -5px rgba(0,0,0,.1)（下拉浮层）
//   --tblr-border-color #e5e7eb（控件边框）/ --tblr-border-color-translucent rgba(4,32,69,.1)（卡片/行分隔）
//   --tblr-border-radius 6px（控件）/ --tblr-border-radius-lg 8px（卡片）
//   --tblr-body-color #1f2937（正文）/ gray-500 #6b7280（次要）/ gray-400 #9ca3af（弱化）
//   --tblr-bg-surface #ffffff（卡片/侧栏/顶栏底）/ gray-50 #f9fafb（页面底/表头/卡片尾/头像底）
//   控件标准：高 40px、padding 9px 16px、14px；表单标签 14px/500（官方不用 13px 弱化）
//   input focus：border #82B7E8 + ring rgba(6,111,209,.25)；下拉浮层 radius 6 + 三层阴影
//   侧栏：官方默认深色（layout-vertical.html）；用户明确不要深色/不要透明 → 实底白 + hairline 分隔
//   （语义 = 官方浅色 navbar 白底，菜单选中透明底仅文字变深灰 #374151，无蓝底）
import type { ThemeConfig } from 'antd';

export const tablerTheme: ThemeConfig = {
  token: {
    // Brand（官方 primary #066fd1 / primary-darken #0563BC）
    colorPrimary: '#066fd1',
    colorPrimaryActive: '#0563BC', // 官方 --tblr-primary-darken（按钮按压）
    colorPrimaryHover: '#0563BC', // 官方按钮 hover 用 darken，非 link-hover
    // Surface（官方：页面底 gray-50 #f9fafb / 卡片白 / 浮层白）
    colorBgLayout: '#f9fafb',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    // Text（官方 gray：800 #1f2937 / 500 #6b7280 / 400 #9ca3af）
    colorText: '#1f2937',
    colorTextHeading: '#1f2937',
    colorTextSecondary: '#6b7280',
    colorTextTertiary: '#9ca3af',
    colorTextDisabled: '#9ca3af',
    // Border（官方：控件灰 #e5e7eb / 卡片与行分隔半透明深蓝 rgba(4,32,69,.1)）
    colorBorder: '#e5e7eb',
    colorBorderSecondary: 'rgba(4,32,69,0.1)',
    colorSplit: 'rgba(4,32,69,0.1)',
    // Semantic（官方 $blue/$green/$yellow/$red/$azure）
    colorSuccess: '#2fb344',
    colorWarning: '#f59f00',
    colorError: '#d63939',
    colorInfo: '#4299e1',
    colorLink: '#066fd1',
    colorLinkHover: '#045db0',
    // 尺度（官方：控件 6 / 卡片 8 / 控件高 40）
    borderRadius: 6,
    controlHeight: 40,
    // 阴影（官方 --tblr-shadow-card 极淡；antd Card 读 boxShadowCard 全局 token）
    boxShadowCard: '0 0 4px rgba(31,41,55,0.04)', // 官方 card 阴影
    boxShadow: '0 1px 1px rgba(31,41,55,0.06)', // 官方 shadow-input（按钮/输入框微阴影基线）
    boxShadowSecondary: '0 16px 24px 2px rgba(0,0,0,0.07), 0 6px 30px 5px rgba(0,0,0,0.06), 0 8px 10px -5px rgba(0,0,0,0.1)', // 官方 --tblr-shadow-dropdown（下拉浮层）
    fontSize: 14,
    fontFamily:
      '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif',
  },
  components: {
    Button: {
      fontWeight: 500,
      borderRadius: 6,
      controlHeight: 40,
      primaryShadow: '0 1px 1px rgba(31,41,55,0.06)', // --tblr-shadow-input
      defaultShadow: '0 1px 1px rgba(31,41,55,0.06)',
      defaultBorderColor: '#e5e7eb', // 默认按钮白底灰边
      defaultBg: '#ffffff',
    },
    Card: {
      borderRadiusLG: 8,
      borderColor: 'rgba(4,32,69,0.1)', // --tblr-border-color-translucent
      boxShadow: '0 0 4px rgba(31,41,55,0.04)', // --tblr-shadow-card
      headerBg: 'transparent',
      headerPadding: '16px 20px',
      bodyPadding: '16px 20px', // 官方 card-body padding 16px 20px（非 antd 默认 24px）
    },
    Table: {
      headerBg: '#f9fafb', // 官方表头 gray-50
      headerColor: '#6b7280', // gray-500
      headerFontSize: 12,
      // rowHoverBg 必须用不透明色：antd 行 hover 会把该色应用到固定列 td，
      // 半透明色会失去遮罩导致底下横向滚动内容"穿透"固定列（Tabler 老毛病，Claude 用不透明 #f5f0e8 无此问题）。
      // 官方半透明 rgba(4,32,69,.03) 叠白底后 ≈ #f7f8f9，观感一致。
      rowHoverBg: '#f7f8f9',
      borderColor: 'rgba(4,32,69,0.1)', // 行分隔半透明深蓝
      cellPaddingBlock: 12,
      cellPaddingInline: 12,
    },
    Layout: {
      siderBg: '#ffffff', // 官方浅色 navbar 白底（用户拍板：不深色、不透明）
      headerBg: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      // 选中：品牌蓝字 + 官方 --tblr-active-bg 淡蓝底（0.04 太淡几乎不可见，用 0.09 语义接近且能一眼看出当前页；
      // 用户明确要求"表示当前所在页的选中效果"，v3 曾改透明底灰字导致看不出选中，已回退）
      itemSelectedBg: 'rgba(6,111,209,0.09)',
      itemSelectedColor: '#066fd1',
      itemColor: '#6b7280', // gray-500 未选中
      itemHoverColor: '#1f2937',
      itemHoverBg: 'rgba(4,32,69,0.03)',
      // 父级 submenu 标题：子项选中时同步品牌蓝（+700 加粗由 CSS 强化，见 global.css）
      subMenuItemSelectedColor: '#066fd1',
      itemBorderRadius: 6,
    },
    Tabs: {
      cardBg: '#f9fafb',
      itemColor: '#6b7280',
      itemHoverColor: '#066fd1',
      itemSelectedColor: '#066fd1',
    },
    Descriptions: {
      labelBg: '#f9fafb', // 官方表头/卡片尾 gray-50
    },
    Select: {
      optionSelectedBg: 'rgba(6,111,209,0.09)',
      optionActiveBg: 'rgba(4,32,69,0.03)',
      colorBgContainer: '#ffffff',
    },
    Input: {
      colorBgContainer: '#ffffff',
      boxShadow: '0 1px 1px rgba(31,41,55,0.06)', // --tblr-shadow-input
      activeShadow: '0 0 0 2px rgba(6,111,209,0.25)', // focus ring
    },
    DatePicker: { colorBgContainer: '#ffffff' },
    Modal: { borderRadiusLG: 8 },
    Tag: { borderRadiusSM: 4 },
    Avatar: {
      colorTextLightSolid: '#6b7280', // 官方头像文字 gray-500
    },
  },
};

// CSS 变量：供 global.css / 壳层硬编码引用
export const tablerCssVars: Record<string, string> = {
  '--brand': '#066fd1',
  '--brand-hover': '#0563BC',
  '--brand-active': '#0563BC',
  '--layout-bg': '#f9fafb',
  '--card-bg': '#ffffff',
  '--card-shadow': '0 0 4px rgba(31,41,55,0.04)', // 官方 --tblr-shadow-card
  '--control-shadow': '0 1px 1px rgba(31,41,55,0.06)', // 官方 --tblr-shadow-input（输入框/下拉/日期静态微阴影）
  '--surface-elevated': '#ffffff', // 顶栏/标签栏/操作栏（官方 bg-surface）
  '--sider-bg': '#ffffff', // 侧栏：官方浅色 navbar 白底（用户拍板）
  '--border': '#e5e7eb',
  '--border-soft': 'rgba(4,32,69,0.1)',
  '--text': '#1f2937',
  '--text-secondary': '#6b7280',
  '--text-tertiary': '#9ca3af',
  '--detail-label-bg': '#f9fafb',
  '--menu-selected-bg': 'rgba(6,111,209,0.09)',
  '--menu-selected-text': '#066fd1',
  '--avatar-bg': '#f9fafb', // 官方头像底 gray-50（非品牌色）
};
