import { useEffect, useMemo, useState } from "react";
import {
  defaultDropAnimationSideEffects,
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
  type DropAnimation,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { Plus } from "lucide-react";
import toast from "react-hot-toast";

import { useDeleteOrder, useMoveOrder, useOrders } from "../lib/queries";
import KanbanColumn from "../components/KanbanColumn";
import OrderCard from "../components/OrderCard";
import NewOrderDrawer from "../components/NewOrderDrawer";
import ConfirmDialog from "../components/ConfirmDialog";
import { STATUS_ORDER } from "../lib/types";
import type { OrderListRow, OrderStatus } from "../lib/types";

type ColumnOrder = Record<OrderStatus, number[]>;

const STORAGE_KEY = "crm-column-order-v1";

const emptyOrder = (): ColumnOrder => ({
  PENDING: [],
  IN_PRODUCTION: [],
  READY: [],
  DELIVERED: [],
  CANCELLED: [],
});

const dropAnimation: DropAnimation = {
  duration: 280,
  easing: "cubic-bezier(0.2, 0.9, 0.3, 1.2)",
  sideEffects: defaultDropAnimationSideEffects({
    styles: { active: { opacity: "0" } },
  }),
};

export default function CRM() {
  const { data, isLoading, isError } = useOrders();
  const move = useMoveOrder();
  const del = useDeleteOrder();

  const [activeId, setActiveId] = useState<number | null>(null);
  const [newOrderOpen, setNewOrderOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<OrderListRow | null>(null);
  const [columnOrder, setColumnOrder] = useState<ColumnOrder>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return emptyOrder();
      const parsed = JSON.parse(raw) as ColumnOrder;
      return { ...emptyOrder(), ...parsed };
    } catch {
      return emptyOrder();
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(columnOrder));
  }, [columnOrder]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  // Group server orders by status, then apply the per-column manual ordering
  // stored in localStorage. Cards we've never seen before get prepended (newest
  // on top); cards in the stored order keep their position.
  const grouped = useMemo<Record<OrderStatus, OrderListRow[]>>(() => {
    const out = emptyOrder() as unknown as Record<OrderStatus, OrderListRow[]>;
    STATUS_ORDER.forEach((s) => (out[s] = []));
    data?.results.forEach((o) => out[o.status].push(o));

    for (const s of STATUS_ORDER) {
      const byId = new Map(out[s].map((o) => [o.id, o]));
      const stored = columnOrder[s] ?? [];
      const ordered: OrderListRow[] = [];
      for (const id of stored) {
        const o = byId.get(id);
        if (o) {
          ordered.push(o);
          byId.delete(id);
        }
      }
      // Anything left in byId is new — show on top.
      out[s] = [...byId.values(), ...ordered];
    }
    return out;
  }, [data, columnOrder]);

  const activeOrder =
    activeId != null
      ? data?.results.find((o) => o.id === activeId) ?? null
      : null;

  const onDragStart = (e: DragStartEvent) => {
    setActiveId(Number(e.active.id));
  };

  const findStatusOf = (id: number | string): OrderStatus | null => {
    if (typeof id === "string" && (STATUS_ORDER as string[]).includes(id)) {
      return id as OrderStatus;
    }
    const numeric = Number(id);
    return data?.results.find((o) => o.id === numeric)?.status ?? null;
  };

  const onDragEnd = (e: DragEndEvent) => {
    setActiveId(null);
    const aId = Number(e.active.id);
    const overId = e.over?.id;
    if (overId === undefined) return;

    const sourceStatus = data?.results.find((o) => o.id === aId)?.status;
    const targetStatus = findStatusOf(overId);
    if (!sourceStatus || !targetStatus) return;

    if (sourceStatus === targetStatus) {
      // --- Reorder within the same column ----------------------------------
      const ids = grouped[sourceStatus].map((o) => o.id);
      const oldIdx = ids.indexOf(aId);
      const overNumeric = typeof overId === "number" ? overId : Number(overId);
      const newIdx = Number.isNaN(overNumeric)
        ? ids.length - 1
        : ids.indexOf(overNumeric);
      if (oldIdx < 0 || newIdx < 0 || oldIdx === newIdx) return;
      setColumnOrder((prev) => ({
        ...prev,
        [sourceStatus]: arrayMove(ids, oldIdx, newIdx),
      }));
      return;
    }

    // --- Cross-column move: hit the API + update local order ---------------
    move.mutate(
      { id: aId, status: targetStatus },
      {
        onError: (err: unknown) =>
          toast.error(err instanceof Error ? err.message : "Move failed"),
      }
    );

    setColumnOrder((prev) => {
      const sourceList = (prev[sourceStatus] ?? []).filter((id) => id !== aId);
      const targetList = (prev[targetStatus] ?? []).filter((id) => id !== aId);
      // If dropped on a specific card in the target column, slot in there.
      const overNumeric = typeof overId === "number" ? overId : Number(overId);
      let insertAt = targetList.length;
      if (!Number.isNaN(overNumeric)) {
        const idx = targetList.indexOf(overNumeric);
        if (idx >= 0) insertAt = idx;
      }
      const nextTarget = [
        ...targetList.slice(0, insertAt),
        aId,
        ...targetList.slice(insertAt),
      ];
      return { ...prev, [sourceStatus]: sourceList, [targetStatus]: nextTarget };
    });
  };

  return (
    <div className="space-y-6">
      <header className="sticky top-0 z-20 -mx-10 px-10 py-4 bg-white/80 backdrop-blur-md border-b border-lavender-100 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">CRM Board</h1>
          <p className="text-ink-soft mt-1">
            Drag across columns to change status, or within a column to reorder.
          </p>
        </div>
        <button
          onClick={() => setNewOrderOpen(true)}
          className="btn btn-primary flex-shrink-0"
        >
          <Plus className="w-4 h-4" />
          New order
        </button>
      </header>

      {isLoading && <div className="text-ink-soft">Loading…</div>}
      {isError && <div className="text-rose-600">Failed to load orders.</div>}

      {!isLoading && !isError && (
        <DndContext
          sensors={sensors}
          onDragStart={onDragStart}
          onDragEnd={onDragEnd}
          onDragCancel={() => setActiveId(null)}
        >
          <div className="flex gap-5 overflow-x-auto pb-6 -mx-2 px-2">
            {STATUS_ORDER.map((s) => (
              <KanbanColumn
                key={s}
                status={s}
                orders={grouped[s]}
                onDelete={setPendingDelete}
              />
            ))}
          </div>
          <DragOverlay dropAnimation={dropAnimation}>
            {activeOrder ? <OrderCard order={activeOrder} dragging /> : null}
          </DragOverlay>
        </DndContext>
      )}

      <NewOrderDrawer
        open={newOrderOpen}
        onClose={() => setNewOrderOpen(false)}
      />

      <ConfirmDialog
        open={pendingDelete != null}
        title="Delete this order?"
        message={
          pendingDelete
            ? `Order #${pendingDelete.id} for ${pendingDelete.customer_name} will be permanently removed, along with its line items, measurements, and tickets.`
            : ""
        }
        confirmLabel="Delete order"
        destructive
        loading={del.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!pendingDelete) return;
          del.mutate(pendingDelete.id, {
            onSuccess: () => {
              toast.success("Order deleted");
              setPendingDelete(null);
            },
            onError: (err: unknown) =>
              toast.error(err instanceof Error ? err.message : "Delete failed"),
          });
        }}
      />
    </div>
  );
}
