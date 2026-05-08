import { Calendar, Package, Trash2 } from "lucide-react";
import { differenceInCalendarDays, format, parseISO } from "date-fns";

import { formatMoney, STATUS_COLORS } from "../lib/types";
import type { OrderListRow } from "../lib/types";

interface Props {
  order: OrderListRow;
  /** When the card is being dragged via dnd-kit */
  dragging?: boolean;
  /** When set, shows a hover-revealed trash icon. */
  onDelete?: (order: OrderListRow) => void;
}

export default function OrderCard({ order, dragging = false, onDelete }: Props) {
  const due = parseISO(order.due_date);
  const days = differenceInCalendarDays(due, new Date());
  const overdue = days < 0;
  const colors = STATUS_COLORS[order.status];

  return (
    <div
      className={[
        "group card p-4 transition-all duration-200 relative",
        dragging
          ? "shadow-glow-lg scale-[1.02] rotate-[1.5deg]"
          : "hover:shadow-glow",
      ].join(" ")}
    >
      {onDelete && (
        <button
          type="button"
          // Stop the dnd-kit pointer sensor from interpreting this click as a drag.
          onPointerDown={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            onDelete(order);
          }}
          className="absolute top-2 right-2 w-7 h-7 rounded-lg flex items-center justify-center text-ink-soft opacity-0 group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-600 transition-all duration-150"
          title="Delete order"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      )}

      <div className="flex items-start justify-between gap-3 pr-6">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-ink truncate">
            {order.customer_name}
          </div>
          <div className="text-xs text-ink-soft mt-0.5">#{order.id}</div>
        </div>
        <span
          className={`pill ${colors.bg} ${colors.text} ring-1 ${colors.ring}`}
        >
          {order.status_label}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-3 text-xs text-ink-soft">
        <span className="inline-flex items-center gap-1">
          <Package className="w-3.5 h-3.5" />
          {order.item_count} {order.item_count === 1 ? "item" : "items"}
        </span>
        <span
          className={[
            "inline-flex items-center gap-1",
            overdue && order.status !== "DELIVERED" && order.status !== "CANCELLED"
              ? "text-rose-600 font-medium"
              : "",
          ].join(" ")}
        >
          <Calendar className="w-3.5 h-3.5" />
          {format(due, "MMM d")}
          {overdue && order.status !== "DELIVERED" && order.status !== "CANCELLED"
            ? ` · ${Math.abs(days)}d late`
            : days >= 0
            ? ` · ${days}d`
            : ""}
        </span>
      </div>

      <div className="mt-2.5 text-sm font-semibold text-lavender-700">
        {formatMoney(order.total_price, order.currency)}
      </div>
    </div>
  );
}
