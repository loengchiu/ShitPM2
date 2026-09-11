// 视觉口径（2026-09-11 v3 拍板）：**颜色留 Tabler，其余全按 antd 官方默认**。
// 本文件只保留颜色体系（Tabler 官方 CSS 解引用值）；尺寸 / 字号 / 字体 / 阴影 /
// 圆角等非颜色 token 一律不再覆盖，由 antd v6 官方默认值自己生效。
// 来源（颜色）：Tabler 官方 CSS（preview.tabler.io/dist/css/tabler.min.css，--tblr-* 变量直接解引用）
//   --tblr-primary #066fd1 / --tblr-primary-darken rgb(5.4,99.9,188.1)≈#0563BC（按钮 hover/active）
//   --tblr-border-color #e5e7eb（控件边框）/ --tblr-border-color-translucent rgba(4,32,69,.1)（卡片/行分隔）
//   --tblr-body-color #1f2937（正文）/ gray-500 #6b7280（次要）/ gray-400 #9ca3af（弱化）
//   --tblr-bg-surface #ffffff（卡片/侧栏/顶栏底）/ gray-50 #f9fafb（页面底/表头/卡片尾）
//   侧栏：官方默认深色（layout-vertical.html）；用户明确不要深色/不要透明 → 实底白 + hairline 分隔
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
    // 尺寸 / 字体 / 阴影 / 圆角：不覆盖，走 antd 官方默认
    // （2026-09-11 v3：删除 controlHeight 40 / fontSize / fontFamily / borderRadius /
    //  boxShadow* 全部 Tabler 值；控件高度 32、表头字号 14、单元格 padding 16、
    //  卡片 padding 24、阴影黑基均由官方默认生效）
  },
  components: {
    Card: {
      borderColor: 'rgba(4,32,69,0.1)', // --tblr-border-color-translucent（颜色，保留）
    },
    Table: {
      headerBg: '#f9fafb', // 官方表头 gray-50（颜色）
      headerColor: '#6b7280', // gray-500（颜色）
      // rowHoverBg 必须用不透明色：antd 行 hover 会把该色应用到固定列 td，
      // 半透明色会失去遮罩导致底下横向滚动内容"穿透"固定列。
      // 官方半透明 rgba(4,32,69,.03) 叠白底后 ≈ #f7f8f9，观感一致。
      rowHoverBg: '#f7f8f9',
      borderColor: 'rgba(4,32,69,0.1)', // 行分隔半透明深蓝（颜色）
      // headerFontSize / cellPaddingBlock / cellPaddingInline：删，走官方默认 14 / 16 / 16
    },
    Layout: {
      siderBg: '#ffffff', // 官方浅色 navbar 白底（用户拍板：不深色、不透明）
      headerBg: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      // 选中：品牌蓝字 + 淡蓝底（0.04 太淡几乎不可见，用 0.09 语义接近且能一眼看出当前页；
      // 用户明确要求"表示当前所在页的选中效果"）
      itemSelectedBg: 'rgba(6,111,209,0.09)',
      itemSelectedColor: '#066fd1',
      itemColor: '#6b7280', // gray-500 未选中
      itemHoverColor: '#1f2937',
      itemHoverBg: 'rgba(4,32,69,0.03)',
      // 父级 submenu 标题：子项选中时同步品牌蓝（+700 加粗由 CSS 强化，见 global.css）
      subMenuItemSelectedColor: '#066fd1',
      // itemBorderRadius：删，走官方默认
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
      // boxShadow / activeShadow：删，走官方默认
    },
    DatePicker: { colorBgContainer: '#ffffff' },
    // Button / Modal / Tag / Avatar 的尺寸与阴影覆盖：删，走官方默认
    // （Avatar 改品牌色底 + 白字，见 tablerCssVars --avatar-bg）
  },
};

// CSS 变量：供 global.css / 壳层硬编码引用（仅颜色；阴影交官方默认，变量已删）
export const tablerCssVars: Record<string, string> = {
  '--brand': '#066fd1',
  '--brand-hover': '#0563BC',
  '--brand-active': '#0563BC',
  '--layout-bg': '#f9fafb',
  '--card-bg': '#ffffff',
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
  '--avatar-bg': '#066fd1', // 品牌色底 + 白字（§2.3 角色切换器）
};
