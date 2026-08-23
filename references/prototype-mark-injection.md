# Prototype Mark 标注注入写法（Vite 源码工程版）

> 只用于 `output/prototypemark/` 副本，不修改原始 `output/prototype/`。
> 标注内容是 Design/PRD 内容的展示载体，不是新事实源。

## 目录

- [注入目标](#注入目标)
- [标注数据](#标注数据)
- [MarkLayer 组件](#marklayer-组件)
- [角标定位与弹窗规则](#角标定位与弹窗规则)
- [硬规则](#硬规则)

## 注入目标

把标注系统注入到 `output/prototypemark/` 的 React 源码工程中：

1. `src/shared/pm/annotations.js`：标注数据（编号 → 标题 + 内容）
2. `src/shared/pm/MarkLayer.jsx`：角标 + 浮窗组件（见下）
3. 业务页面 JSX 目标元素加 `data-pm-mark="N"`（或页面级 `data-pm-mark-page="N"`）
4. `src/App.jsx` 挂载 `<MarkLayer />`
5. 复制工程内运行 `npm ci` + `npm run build`，输出 `output/prototypemark/dist/`

定位规则（与旧版一致）：

- 列表/表格 → 标注容器（Card、Table 父 div），不标注每一行
- 按钮/操作区 → 按钮组的父容器
- 表单 → `<Form>` 或最外层 `<div>`
- 页面级 → 页面容器加 `data-pm-mark-page="N"`
- 只做 `data-pm-mark` 属性插入，不修改现有 class、结构、content

## 标注数据

`src/shared/pm/annotations.js`：

```js
// 内容字段用单引号包裹；内部中文引号保留原样；英文单引号用 \' 转义
export const PM_ANNOTATIONS = {
  1: { title: '筛选条件区', content: '所有筛选条件…' },
  2: { title: '操作栏', content: '编辑/删除/查看…' },
};
```

## MarkLayer 组件

`src/shared/pm/MarkLayer.jsx`（角标统一 `position: fixed` + 挂载到 `document.body`）：

```jsx
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { PM_ANNOTATIONS } from './annotations.js';

const BADGE_CLASS = 'pm-badge';
const POPUP_CLASS = 'pm-popup';

function getContainerClass(target) {
  if (target.closest('.ant-drawer, [class*="drawer"]')) return 'pm-badge-in-drawer';
  if (target.closest('.ant-modal, [class*="modal"], [class*="dialog"]')) return 'pm-badge-in-modal';
  return 'pm-badge-in-page';
}

function collectTargets() {
  const list = [];
  document.querySelectorAll('[data-pm-mark], [data-pm-mark-page]').forEach((el) => {
    const id = el.getAttribute('data-pm-mark') || el.getAttribute('data-pm-mark-page');
    if (id && PM_ANNOTATIONS[id]) {
      list.push({ id, el });
    }
  });
  return list;
}

export default function MarkLayer() {
  const [marks, setMarks] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [popupPos, setPopupPos] = useState({ top: 0, left: 0 });
  const popupRef = useRef(null);

  const renderMarks = () => {
    setMarks(collectTargets());
  };

  useEffect(() => {
    renderMarks();
    const onResizeOrScroll = () => renderMarks();
    const observer = new MutationObserver(() => {
      // 容器可见性状态：抽屉/弹窗打开时隐藏主页角标
      const drawer = document.querySelector('.ant-drawer-open');
      const modal = document.querySelector('.ant-modal-wrap');
      document.body.classList.toggle('pm-drawer-open', !!drawer);
      document.body.classList.toggle('pm-modal-open', !!modal);
      renderMarks();
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'style'],
    });
    window.addEventListener('resize', onResizeOrScroll);
    window.addEventListener('scroll', onResizeOrScroll, true);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', onResizeOrScroll);
      window.removeEventListener('scroll', onResizeOrScroll, true);
    };
  }, []);

  const togglePopup = (id, el) => {
    if (openId === id) {
      setOpenId(null);
      return;
    }
    const rect = el.getBoundingClientRect();
    let top = rect.bottom + 8;
    let left = rect.left;
    const width = 450;
    if (left + width > window.innerWidth - 8) left = Math.max(8, window.innerWidth - width - 8);
    if (top + 320 > window.innerHeight) top = Math.max(8, rect.top - 320);
    setPopupPos({ top, left });
    setOpenId(id);
  };

  return createPortal(
    <>
      {marks.map(({ id, el }) => {
        const rect = el.getBoundingClientRect();
        const container = getContainerClass(el);
        if (!rect.width && !rect.height) return null;
        return (
          <button
            key={id}
            type="button"
            className={`${BADGE_CLASS} ${container}`}
            style={{ top: rect.top - 8, left: rect.right - 14 }}
            onClick={(event) => {
              event.stopPropagation();
              togglePopup(id, el);
            }}
          >
            {id}
          </button>
        );
      })}
      {openId && (
        <div
          ref={popupRef}
          className={POPUP_CLASS}
          style={{ ...popupPos, display: 'block' }}
          onClick={(event) => event.stopPropagation()}
        >
          <div className="pm-popup-head">
            <span className="pm-popup-title">
              [{openId}] {PM_ANNOTATIONS[openId].title}
            </span>
            <span className="pm-popup-close" onClick={() => setOpenId(null)}>×</span>
          </div>
          <div className="pm-popup-body">{PM_ANNOTATIONS[openId].content}</div>
          <div className="pm-popup-source">内容来源：Design 文件或 prd.md（由标注时标注）</div>
        </div>
      )}
    </>,
    document.body,
  );
}
```

配套 CSS（注入 `src/styles/pm.css` 并在 `main.jsx` 引入，或写在 `global.css` 末尾）：

```css
.pm-badge {
  position: fixed;
  z-index: 9998;
  display: inline-block;
  background: rgb(250, 173, 20);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 14px;
  padding: 0 4px;
  border-radius: 2px;
  cursor: pointer;
  border: none;
  pointer-events: auto;
}
.pm-popup {
  position: fixed;
  z-index: 99999;
  width: 450px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  background: #f0efef;
  border-radius: 4px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
}
.pm-popup-head {
  position: sticky;
  top: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f0efef;
}
.pm-popup-title {
  font-weight: 700;
  font-size: 13px;
}
.pm-popup-close {
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}
.pm-popup-body {
  padding: 0 12px 12px;
  font-size: 13px;
  line-height: 1.6;
}
.pm-popup-source {
  padding: 8px 12px;
  font-size: 11px;
  color: #8c8c8c;
  border-top: 1px solid #e0e0e0;
}
body.pm-drawer-open .pm-badge.pm-badge-in-page,
body.pm-modal-open .pm-badge.pm-badge-in-page {
  display: none;
}
```

## 角标定位与弹窗规则

1. 角标一律 `position: fixed` + `document.body` 挂载（React `createPortal`）；禁止 `position: absolute`、禁止插入目标元素内部
2. 坐标：`top = rect.top - 8`，`left = rect.right - 14`（角标右边缘对齐目标元素右边缘）
3. 弹窗：点击角标打开（非 hover），再次点击同一角标关闭；X 按钮关闭；点击页面空白处关闭所有
4. 浮窗默认 `top: badgeRect.bottom + 8; left: badgeRect.left`；右超左移、下超上移、不够贴顶 16px
5. 抽屉/弹窗打开时隐藏主页角标（body class 控制），同一编号只能开一个浮窗
6. 浮窗内容必须标注“内容来源：Design 文件”或“内容来源：prd.md”，不承诺脱离源文件后仍是权威规格

## 硬规则

- 不反写 prd.md / Design 文件；编号 [N] 只存在于 prototypemark 副本
- 不修改 `output/prototype/`；只操作 `output/prototypemark/`
- 不引入外部 CDN；标注组件全部本地实现
- 不进入 review 链路；不生成 metadata
- 高影响意见（缺失模块、错误状态、权限漏洞等）不直接修改 Prototype 或 Design，按“高影响反馈结构化输出约定”输出意见清单，建议用户通过 spm-fix 回写 Design
