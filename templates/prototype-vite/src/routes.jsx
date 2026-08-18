import Home from './modules/home/Home.jsx';
import FormDemo from './modules/demo/FormDemo.jsx';
import NotFound from './shared/NotFound.jsx';

// 路由注册表：新增业务页面时在这里登记
// path 为 Hash 路径（如 /plan/list）；menu: true 时出现在侧栏菜单
export const routes = [
  { path: '/', title: '首页', component: Home, menu: true },
  { path: '/demo-form', title: '示例表单', component: FormDemo, menu: true },
  { path: '*', title: '页面不存在', component: NotFound, menu: false },
];
