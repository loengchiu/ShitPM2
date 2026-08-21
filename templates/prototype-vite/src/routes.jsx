import {
  AccountBookOutlined,
  ApartmentOutlined,
  AppstoreOutlined,
  CalendarOutlined,
  CarOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  ExportOutlined,
  MoneyCollectOutlined,
  ProfileOutlined,
  SafetyCertificateOutlined,
  ScheduleOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import Home from './modules/home/Home.jsx';
import DesignGallery from './modules/demo/DesignGallery.jsx';
import DetailDemo from './modules/demo/DetailDemo.jsx';
import FormDemo from './modules/demo/FormDemo.jsx';
import Placeholder from './modules/demo/Placeholder.jsx';
import NotFound from './shared/NotFound.jsx';

// 路由注册表：新增业务页面时在这里登记
// path 为 Hash 路径；menu: true 时出现在侧栏菜单
// module 为所属主模块（顶栏 Tab）；group 为侧栏二级分组（可选）；icon 为侧栏菜单图标
export const routes = [
  { path: '/', title: '首页', component: Home, menu: true, module: null, pinned: true },
  {
    path: '/gallery',
    title: '设计样张',
    component: DesignGallery,
    menu: true,
    module: '物业管理',
    icon: <AppstoreOutlined />,
  },
  {
    path: '/rent',
    title: '租金清分',
    component: Placeholder,
    menu: true,
    module: '物业管理',
    group: '收费管理',
    icon: <MoneyCollectOutlined />,
    placeholder: '租金清分页面（占位，按 Design 事实生成）',
  },
  {
    path: '/detail',
    title: '商户详情',
    component: DetailDemo,
    menu: true,
    module: '物业管理',
    group: '收费管理',
    icon: <ProfileOutlined />,
  },
  {
    path: '/form-demo',
    title: '出库申请',
    component: FormDemo,
    menu: true,
    module: '物业管理',
    icon: <ExportOutlined />,
  },
  {
    path: '/schedule',
    title: '排班计划',
    component: Placeholder,
    menu: true,
    module: '物业管理',
    group: '排班管理',
    icon: <ScheduleOutlined />,
    placeholder: '排班计划页面（占位，按 Design 事实生成）',
  },
  {
    path: '/attendance',
    title: '考勤管理',
    component: Placeholder,
    menu: true,
    module: '物业管理',
    group: '排班管理',
    icon: <ClockCircleOutlined />,
    placeholder: '考勤管理页面（占位，按 Design 事实生成）',
  },
  {
    path: '/parking-records',
    title: '停车记录',
    component: Placeholder,
    menu: true,
    module: '停车管理',
    group: '日常运营',
    icon: <CarOutlined />,
    placeholder: '停车记录页面（占位，按 Design 事实生成）',
  },
  {
    path: '/parking-spaces',
    title: '车位管理',
    component: Placeholder,
    menu: true,
    module: '停车管理',
    group: '日常运营',
    icon: <EnvironmentOutlined />,
    placeholder: '车位管理页面（占位，按 Design 事实生成）',
  },
  {
    path: '/users',
    title: '用户管理',
    component: Placeholder,
    menu: true,
    module: '系统管理',
    icon: <TeamOutlined />,
    placeholder: '用户管理页面（占位，按 Design 事实生成）',
  },
  {
    path: '/roles',
    title: '角色权限',
    component: Placeholder,
    menu: true,
    module: '系统管理',
    icon: <SafetyCertificateOutlined />,
    placeholder: '角色权限页面（占位，按 Design 事实生成）',
  },
  { path: '*', title: '页面不存在', component: NotFound, menu: false },
];

// 侧栏分组图标映射（group 名 → 图标）
export const groupIcons = {
  收费管理: <AccountBookOutlined />,
  排班管理: <CalendarOutlined />,
  日常运营: <CarOutlined />,
};

// 主模块图标映射（module 名 → 图标）
export const moduleIcons = {
  物业管理: <ApartmentOutlined />,
  停车管理: <CarOutlined />,
  系统管理: <SettingOutlined />,
};
