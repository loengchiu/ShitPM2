import { useId } from 'react';
import { Button, Card, Dropdown, Empty, Space, Table, Tag } from 'antd';
import {
  IconArrowLeft,
  IconInbox,
  IconTrendingDown,
  IconTrendingUp,
  IconDots,
} from '@tabler/icons-react';

// ── 高频共享 UI：只封装稳定的视觉与交互，不承载 Design 业务规则 ──

export function TablerPageHeader({ prefix, title, subtitle, onBack, actions, className = '' }) {
  const reactId = useId();
  const headingId = 'page-title-' + reactId.replace(/:/g, '');
  const subtitleId = subtitle ? headingId + '-description' : undefined;

  return (
    <header className={`page-head ${className}`} aria-labelledby={headingId} aria-describedby={subtitleId}>
      <div className="page-head-main">
        {prefix ? <div className="page-prefix" aria-label="所属模块">{prefix}</div> : null}
        <h1 id={headingId} className="page-title">{title}</h1>
        {subtitle ? <p id={subtitleId} className="page-sub">{subtitle}</p> : null}
      </div>
      <div className="page-head-actions">
        {onBack ? (
          <Button type="text" icon={<IconArrowLeft size={16} />} onClick={onBack}>
            返回
          </Button>
        ) : null}
        {actions}
      </div>
    </header>
  );
}

export function TablerSectionCard({ title, extra, children, className = '' }) {
  return (
    <Card className={`tabler-section-card ${className}`} title={title} extra={extra}>
      {children}
    </Card>
  );
}

const metricTrendIcons = { up: IconTrendingUp, down: IconTrendingDown };

export function TablerMetricCard({ title, value, suffix, trend, trendLabel, icon }) {
  const TrendIcon = metricTrendIcons[trend];
  const trendClass = trend === 'up' ? 'success' : trend === 'down' ? 'error' : '';
  return (
    <Card className="tabler-metric-card">
      <div className="tabler-metric-card-head">
        <span className="tabler-metric-card-title">{title}</span>
        {icon ? <span className="tabler-icon-badge">{icon}</span> : null}
      </div>
      <div className="tabler-metric-card-value">
        {value}
        {suffix ? <span style={{ fontSize: 14, fontWeight: 400, marginLeft: 4 }}>{suffix}</span> : null}
      </div>
      {trendLabel ? (
        <div className={`tabler-metric-card-trend ${trendClass}`}>
          {TrendIcon ? <TrendIcon size={14} style={{ marginRight: 4, verticalAlign: -2 }} /> : null}
          {trendLabel}
        </div>
      ) : null}
    </Card>
  );
}

export function TablerToolbar({ children, actions, className = '' }) {
  return (
    <div className={`tabler-toolbar ${className}`}>
      <div className="tabler-toolbar-main">{children}</div>
      {actions ? <div className="tabler-toolbar-actions">{actions}</div> : null}
    </div>
  );
}

export function TablerDataTable({ emptyTitle, emptyDescription, pagination, className = '', ...tableProps }) {
  const emptyText =
    emptyTitle !== undefined ? (
      <TablerEmptyState
        compact
        icon={<IconInbox size={24} />}
        title={emptyTitle}
        description={emptyDescription}
      />
    ) : undefined;
  const normalizedPagination =
    pagination === false
      ? false
      : {
          pageSize: 10,
          showTotal: (total) => `共 ${total} 条`,
          ...pagination,
        };
  return (
    <Table
      {...tableProps}
      className={`tabler-data-table ${className}`}
      scroll={{ x: 'max-content', ...(tableProps.scroll || {}) }}
      pagination={normalizedPagination}
      locale={emptyText ? { emptyText } : undefined}
    />
  );
}

const statusColorMap = {
  success: { color: 'success', label: '成功' },
  progress: { color: 'processing', label: '进行中' },
  warning: { color: 'warning', label: '警告' },
  error: { color: 'error', label: '失败' },
  weak: { color: 'default', label: '弱状态' },
};

export function TablerStatusTag({ status, text, color }) {
  const mapped = statusColorMap[status] || { color: 'default', label: text || status };
  return <Tag color={color || mapped.color}>{text || mapped.label}</Tag>;
}

export function TablerIconButton({ icon, danger, loading, disabled, ariaLabel, title, onClick }) {
  return (
    <Button
      type="text"
      danger={danger}
      loading={loading}
      disabled={disabled}
      aria-label={ariaLabel}
      title={title}
      icon={icon}
      onClick={onClick}
    />
  );
}

// 表格行操作：≤3 个按钮直接展示，超过 3 个合并进“更多”下拉（Tabler 标准做法）。
// items: [{ key, label, icon, danger, disabled, onClick }]
export function TablerRowActions({ items, maxVisible = 3, className = '' }) {
  const visible = (items || []).slice(0, maxVisible);
  const more = (items || []).slice(maxVisible);
  const menuItems = more.map((it) => ({
    key: it.key || it.label,
    label: it.label,
    icon: it.icon,
    danger: it.danger,
    disabled: it.disabled,
  }));

  return (
    <Space size={0} wrap={false} className={`tabler-row-actions ${className}`}>
      {visible.map((it) => (
        <TablerIconButton
          key={it.key || it.label}
          ariaLabel={it.label}
          title={it.label}
          icon={it.icon}
          danger={it.danger}
          disabled={it.disabled}
          loading={it.loading}
          onClick={it.onClick}
        />
      ))}
      {menuItems.length > 0 ? (
        <Dropdown
          menu={{ items: menuItems, onClick: ({ key }) => {
            const target = more.find((it) => (it.key || it.label) === key);
            if (target && target.onClick) target.onClick();
          } }}
          trigger={['click']}
          placement="bottomRight"
        >
          <TablerIconButton ariaLabel="更多操作" title="更多" icon={<IconDots size={16} />} />
        </Dropdown>
      ) : null}
    </Space>
  );
}

export function TablerFormSection({ title, extra, children, className = '' }) {
  return (
    <Card className={`tabler-form-section ${className}`} title={title} extra={extra}>
      {children}
    </Card>
  );
}

export function TablerEmptyState({ icon, title, description, action, compact, className = '' }) {
  return (
    <Empty
      className={`tabler-empty-state ${compact ? 'compact' : ''} ${className}`}
      image={
        icon ? (
          <span className="tabler-icon-badge">{icon}</span>
        ) : null
      }
      description={
        <span>
          <div style={{ color: 'var(--spm-color-text)', fontWeight: 500 }}>{title || '暂无数据'}</div>
          {description ? (
            <div style={{ color: 'var(--spm-color-text-secondary)' }}>{description}</div>
          ) : null}
        </span>
      }
    >
      {action ? <div className="tabler-empty-state-actions">{action}</div> : null}
    </Empty>
  );
}

export function TablerActionBar({ children }) {
  return <div className="tabler-action-bar">{children}</div>;
}
