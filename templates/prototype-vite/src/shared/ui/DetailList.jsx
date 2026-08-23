// 详情列表：仅改变列宽比例（20/30/20/30 或 20/80），其余观感 = antd Descriptions 原样
// 列宽通过 .detail-list / .detail-list-textarea CSS + table-layout: fixed 控制
// 不要再用 labelStyle/contentStyle：td width 是相对整行，不是相对 item
import { Card, Descriptions } from 'antd';

export default function DetailList({ title, items, variant = 'pair' }) {
  const column = variant === 'pair' ? 2 : 1;
  const className = variant === 'pair' ? 'detail-list' : 'detail-list-textarea';
  const descItems = items.map(({ label, value }) => ({ label, children: value }));
  return (
    <Card className={`${className}-card`} size="small" style={{ marginBottom: 16 }}>
      <Descriptions
        className={className}
        title={title}
        bordered
        size="small"
        column={column}
        items={descItems}
      />
    </Card>
  );
}
