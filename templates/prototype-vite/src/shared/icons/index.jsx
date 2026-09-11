// 图标统一入口（2026-09-11 v3）：全部来自 @ant-design/icons（antd 6 官方图标库）。
// 硬规则：页面与组件一律从 shared/icons 取图标，禁止直接 import '@ant-design/icons'
// 或任何第三方图标库（原 Tabler 图标库已卸载）。
//
// 适配层说明：Tabler 图标用 size 属性定尺寸，antd 图标用 fontSize。
// adapt() 把 size 转成 fontSize 样式，历史调用点（size={16} 等 39 处）无需改动。
//
// 语义最近的登记（antd 无精确对应，不臆造图标名）：
//   IconPackage   → CodeSandboxOutlined（包裹/物资 → 立体箱形）
//   IconBuilding  → BankOutlined（楼宇 → 官方大楼柱式图标）
//   IconMoneybag  → MoneyCollectOutlined（钱袋）
import {
  AppstoreOutlined,
  ArrowLeftOutlined,
  BankOutlined,
  BarChartOutlined,
  CalendarOutlined,
  CarOutlined,
  CheckCircleOutlined,
  CheckOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  CloseOutlined,
  CodeSandboxOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  EllipsisOutlined,
  EnvironmentOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  ExportOutlined,
  FallOutlined,
  FileTextOutlined,
  InboxOutlined,
  LockOutlined,
  MenuOutlined,
  MoneyCollectOutlined,
  PlusOutlined,
  PrinterOutlined,
  ReloadOutlined,
  RiseOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  SendOutlined,
  SettingOutlined,
  TeamOutlined,
  UnorderedListOutlined,
  WarningOutlined,
} from '@ant-design/icons';

// size → fontSize 适配：保留 Tabler 时代的 size 属性调用习惯
function adapt(AntIcon, displayName) {
  function Adapted({ size, style, ...rest }) {
    return <AntIcon {...rest} style={size != null ? { fontSize: size, ...style } : style} />;
  }
  Adapted.displayName = displayName;
  return Adapted;
}

export const IconAlertTriangle = adapt(WarningOutlined, 'IconAlertTriangle');
export const IconApps = adapt(AppstoreOutlined, 'IconApps');
export const IconArrowLeft = adapt(ArrowLeftOutlined, 'IconArrowLeft');
export const IconBuilding = adapt(BankOutlined, 'IconBuilding');
export const IconCalendar = adapt(CalendarOutlined, 'IconCalendar');
export const IconCar = adapt(CarOutlined, 'IconCar');
export const IconChartBar = adapt(BarChartOutlined, 'IconChartBar');
export const IconCheck = adapt(CheckOutlined, 'IconCheck');
export const IconCircleCheck = adapt(CheckCircleOutlined, 'IconCircleCheck');
export const IconCircleX = adapt(CloseCircleOutlined, 'IconCircleX');
export const IconClock = adapt(ClockCircleOutlined, 'IconClock');
export const IconDownload = adapt(DownloadOutlined, 'IconDownload');
export const IconDots = adapt(EllipsisOutlined, 'IconDots');
export const IconEdit = adapt(EditOutlined, 'IconEdit');
export const IconExclamationCircle = adapt(ExclamationCircleOutlined, 'IconExclamationCircle');
export const IconEye = adapt(EyeOutlined, 'IconEye');
export const IconFileDescription = adapt(FileTextOutlined, 'IconFileDescription');
export const IconFileExport = adapt(ExportOutlined, 'IconFileExport');
export const IconInbox = adapt(InboxOutlined, 'IconInbox');
export const IconList = adapt(UnorderedListOutlined, 'IconList');
export const IconLock = adapt(LockOutlined, 'IconLock');
export const IconMenu2 = adapt(MenuOutlined, 'IconMenu2');
export const IconMapPin = adapt(EnvironmentOutlined, 'IconMapPin');
export const IconMoneybag = adapt(MoneyCollectOutlined, 'IconMoneybag');
export const IconPackage = adapt(CodeSandboxOutlined, 'IconPackage');
export const IconPlus = adapt(PlusOutlined, 'IconPlus');
export const IconPrinter = adapt(PrinterOutlined, 'IconPrinter');
export const IconRefresh = adapt(ReloadOutlined, 'IconRefresh');
export const IconSearch = adapt(SearchOutlined, 'IconSearch');
export const IconSend = adapt(SendOutlined, 'IconSend');
export const IconSettings = adapt(SettingOutlined, 'IconSettings');
export const IconShieldCheck = adapt(SafetyCertificateOutlined, 'IconShieldCheck');
export const IconTrash = adapt(DeleteOutlined, 'IconTrash');
export const IconTrendingDown = adapt(FallOutlined, 'IconTrendingDown');
export const IconTrendingUp = adapt(RiseOutlined, 'IconTrendingUp');
export const IconUsers = adapt(TeamOutlined, 'IconUsers');
export const IconX = adapt(CloseOutlined, 'IconX');
