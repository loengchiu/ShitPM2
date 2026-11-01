# Prototype Mark 标注注入写法（Vite 源码工程版）

> 只用于 `output/prototypemark/` 副本，不修改原始 `output/prototype/`。
> 标注文本是选定事实源的展示载体，不新增来源之外的产品事实。

## 目录

- [注入目标](#注入目标)
- [标注数据](#标注数据)
- [MarkLayer 组件](#marklayer-组件)
- [角标定位与弹窗规则](#角标定位与弹窗规则)
- [硬规则](#硬规则)

## 注入目标

把标注系统注入到 `output/prototypemark/` 的 React 源码工程中：

1. `src/shared/pm/annotations.js`：标注数据（编号 → 标题、按需 section、来源和状态）
2. `src/shared/pm/MarkLayer.jsx`：角标 + 浮窗组件（见下）
3. 业务页面 JSX 的目标元素加 `data-pm-mark="N"`（整页规则使用 `data-pm-mark-page="N"`）
4. `src/App.jsx` 挂载 `<MarkLayer />`
5. 复制工程内运行 `npm ci` + `npm run build`，输出 `output/prototypemark/dist/`

定位时优先使用原型已有的语义锚点：

- 页面：`data-page` 或路由登记项；
- 区块：`data-block` / `data-section`；
- 字段：`data-field`；
- 操作：`data-operation`；
- 状态：`data-state`。

`data-pm-mark` 只承担角标编号，不替代业务语义锚点。优先标注最精确的容器：

- 列表/表格 → 表格、卡片或所在区块容器，不标注每一行；
- 按钮/操作区 → 操作组父容器或明确的操作区；
- 表单 → `<Form>` 或字段所在区块；
- 页面级规则 → 页面容器加 `data-pm-mark-page="N"`；
- 只插入 `data-pm-mark`，不修改现有 class、结构或内容。

## 标注数据

`src/shared/pm/annotations.js`：

```js
export const PM_ANNOTATIONS = {
  1: {
    title: '合同操作栏',
    sections: [
      {
        title: '实现规则',
        items: [
          '仅草稿状态可编辑。',
          '删除合同时同步删除关联账单；关联账单删除失败时整体回滚。',
        ],
      },
      {
        title: '权限与数据范围',
        items: ['一线角色不显示删除；管理员仅能删除本服务区合同。'],
      },
      {
        title: '验收判断',
        items: ['审批中合同不显示编辑和删除；关联账单删除失败时合同与账单均保留。'],
      },
    ],
    source: {
      file: 'output/design/合同管理.md',
      section: '合同列表 > 操作栏',
    },
    status: 'confirmed',
  },
  2: {
    title: '盘点任务状态',
    sections: [
      {
        title: '状态与操作',
        items: ['盘点任务超过结束时间后进入超期状态，不允许继续录入。'],
      },
    ],
    source: {
      file: 'output/design/盘点管理.md',
      section: '盘点任务 > 状态与业务规则',
    },
    status: 'pending',
  },
};
```

数据约束：

- `sections` 只放实际存在的内容，不生成空 section；
- `items` 每条表达一个可执行条件、结果或验收判断；
- `source.file` 使用项目相对路径，`source.section` 使用可回读的标题路径；
- `status` 只使用 `confirmed` 或 `pending`，分别显示为“已确认”和“待确认”；
- 一条标注只来自一个事实源，不混合 Design 与 PRD。

## MarkLayer 组件

`src/shared/pm/MarkLayer.jsx`（角标统一 `position: fixed` + 挂载到 `document.body`）：

```jsx
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { PM_ANNOTATIONS } from './annotations.js';

const BADGE_CLASS = 'pm-badge';
const POPUP_CLASS = 'pm-popup';
const STATUS_LABELS = {
  confirmed: '已确认',
  pending: '待确认',
};

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
    const onDocumentClick = () => setOpenId(null);
    const observer = new MutationObserver(() => {
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
    document.addEventListener('click', onDocumentClick);
    window.addEventListener('resize', onResizeOrScroll);
    window.addEventListener('scroll', onResizeOrScroll, true);
    return () => {
      observer.disconnect();
      document.removeEventListener('click', onDocumentClick);
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

  const annotation = openId ? PM_ANNOTATIONS[openId] : null;

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
      {annotation && (
        <div
          ref={popupRef}
          className={POPUP_CLASS}
          style={{ ...popupPos, display: 'block' }}
          onClick={(event) => event.stopPropagation()}
        >
          <div className="pm-popup-head">
            <span className="pm-popup-title">
              [{openId}] {annotation.title}
            </span>
            <span className="pm-popup-close" onClick={() => setOpenId(null)}>×</span>
          </div>
          <div className="pm-popup-body">
            {annotation.sections.map((section) => (
              <section className="pm-section" key={section.title}>
                <div className="pm-section-title">{section.title}</div>
                <ul className="pm-section-list">
                  {section.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
          <div className={`pm-popup-source pm-source-${annotation.status}`}>
            <span>内容来源：{annotation.source.file} / {annotation.source.section}</span>
            <span className="pm-popup-status">
              {STATUS_LABELS[annotation.status] || annotation.status}
            </span>
          </div>
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
.pm-section + .pm-section {
  margin-top: 12px;
}
.pm-section-title {
  font-weight: 700;
}
.pm-section-list {
  margin: 4px 0 0 18px;
  padding: 0;
}
.pm-popup-source {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  font-size: 11px;
  color: #8c8c8c;
  border-top: 1px solid #e0e0e0;
}
.pm-popup-status {
  flex: none;
  font-weight: 700;
}
.pm-source-pending .pm-popup-status {
  color: #d46b08;
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
4. 浮窗默认 `top = targetRect.bottom + 8; left = targetRect.left`；右超左移、下超上移、不够贴顶 8px
5. 抽屉/弹窗打开时隐藏主页角标（body class 控制），同一编号只能开一个浮窗
6. 浮窗显示按需 section、具体来源文件和章节，以及“已确认/待确认”状态

## 硬规则

- 不反写 prd.md / Design 文件；编号 [N] 只存在于 prototypemark 副本
- 不修改 `output/prototype/`；只操作 `output/prototypemark/`
- 不引入外部 CDN；标注组件全部本地实现
- 不进入 review 链路；不生成 metadata
- 高影响意见（缺失模块、错误状态、权限漏洞等）不直接修改 Prototype 或 Design，按“高影响反馈结构化输出约定”输出意见清单，建议用户通过 spm-fix 回写 Design
