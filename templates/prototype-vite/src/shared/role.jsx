// 角色与权限的演示承载（§2.3 角色切换器 + §5.3 角色差异验收）。
// 原型中角色仅用于评审演示：切换不刷新页面；无权限的菜单/按钮不渲染（不置灰）。
// 高影响权限事实（数据范围、审批链、谁能删谁、跨组织可见性）不在原型里推断，见
// references/prototype-role-permission.md（T-3 落盘）。
import { createContext, useContext } from 'react';

export const ROLES = [
  { key: 'admin', name: '管理员' },
  { key: 'manager', name: '主管' },
  { key: 'operator', name: '一线操作员' },
];

export const RoleContext = createContext(ROLES[0]);

export function useRole() {
  return useContext(RoleContext);
}

// 菜单可见性：route 未声明 roles = 全员可见；声明了则只允许列出的角色
export function canSeeMenu(role, route) {
  return !route.roles || route.roles.includes(role.key);
}
