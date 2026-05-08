import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import OrderCard from "./OrderCard";
import { STATUS_COLORS, STATUS_LABELS } from "../lib/types";
import type { OrderListRow, OrderStatus } from "../lib/types";

interface Props {
  status: OrderStatus;
  orders: OrderListRow[];
  onDelete?: (order: OrderListRow) => void;
}

const DOT_COLORS: Record<OrderStatus, string> = {
  PENDING: "bg-amber-400",
  IN_PRODUCTION: "bg-lavender-500",
  READY: "bg-emerald-400",
  DELIVERED: "bg-slate-400",
  CANCELLED: "bg-rose-400",
};

export default function KanbanColumn({ status, orders, onDelete }: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: { type: "column", status },
  });
  const colors = STATUS_COLORS[status];

  return (
    <div className="flex flex-col w-[300px] flex-shrink-0">
      <div className="flex items-center justify-between px-1 mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${DOT_COLORS[status]}`} />
          <h3 className="text-sm font-semibold text-ink">
            {STATUS_LABELS[status]}
          </h3>
          <span className={`pill ${colors.bg} ${colors.text}`}>
            {orders.length}
          </span>
        </div>
      </div>
      <SortableContext
        items={orders.map((o) => o.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          ref={setNodeRef}
          className={[
            "flex-1 min-h-[400px] rounded-2xl p-3 space-y-3 transition-all duration-200 border-2",
            isOver
              ? "bg-lavender-50/80 border-lavender-300 border-dashed shadow-glow"
              : "bg-surface/40 border-transparent",
          ].join(" ")}
        >
          {orders.map((o) => (
            <SortableOrder key={o.id} order={o} onDelete={onDelete} />
          ))}
          {orders.length === 0 && (
            <div className="text-xs text-ink-soft text-center py-8 border-2 border-dashed border-lavender-100 rounded-xl">
              Drop here
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  );
}

function SortableOrder({
  order,
  onDelete,
}: {
  order: OrderListRow;
  onDelete?: (order: OrderListRow) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: order.id, data: { status: order.status } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    // Hide the source element while dragging — DragOverlay handles the visual
    // and animates it back to this slot on drop.
    opacity: isDragging ? 0 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="cursor-grab active:cursor-grabbing"
    >
      <OrderCard order={order} onDelete={onDelete} />
    </div>
  );
}
