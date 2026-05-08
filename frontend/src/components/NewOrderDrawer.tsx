import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import toast from "react-hot-toast";

import { useCreateOrder, useCustomers } from "../lib/queries";
import type { Currency } from "../lib/types";

const GARMENT_TYPES = [
  { value: "DRESS", label: "Dress" },
  { value: "SUIT", label: "Suit" },
  { value: "SHIRT", label: "Shirt" },
  { value: "PANTS", label: "Pants" },
  { value: "SKIRT", label: "Skirt" },
  { value: "ALTERATION", label: "Alteration" },
  { value: "OTHER", label: "Other" },
];

interface ItemDraft {
  garment_type: string;
  description: string;
  quantity: number;
  unit_price: string;
  fabric: string;
  color: string;
  design_notes: string;
}

const emptyItem = (): ItemDraft => ({
  garment_type: "DRESS",
  description: "",
  quantity: 1,
  unit_price: "0.00",
  fabric: "",
  color: "",
  design_notes: "",
});

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function NewOrderDrawer({ open, onClose }: Props) {
  const [customerId, setCustomerId] = useState<number | "">("");
  const [search, setSearch] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [currency, setCurrency] = useState<Currency>("EUR");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<ItemDraft[]>([emptyItem()]);

  const customersQ = useCustomers(search);
  const createOrder = useCreateOrder();

  const selectedCustomer = useMemo(
    () =>
      customerId === ""
        ? null
        : customersQ.data?.results.find((c) => c.id === customerId) ?? null,
    [customerId, customersQ.data]
  );

  useEffect(() => {
    if (open) {
      // Default due date = 14 days from today.
      const d = new Date();
      d.setDate(d.getDate() + 14);
      setDueDate(d.toISOString().slice(0, 10));
    } else {
      setCustomerId("");
      setSearch("");
      setNotes("");
      setItems([emptyItem()]);
    }
  }, [open]);

  const updateItem = (idx: number, patch: Partial<ItemDraft>) => {
    setItems((prev) => prev.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId) {
      toast.error("Pick a customer.");
      return;
    }
    if (!items.some((it) => it.description.trim())) {
      toast.error("At least one item with a description.");
      return;
    }
    createOrder.mutate(
      {
        customer_id: Number(customerId),
        due_date: dueDate,
        currency,
        notes,
        items_input: items
          .filter((it) => it.description.trim())
          .map((it) => ({
            garment_type: it.garment_type,
            description: it.description,
            quantity: it.quantity,
            unit_price: it.unit_price,
            fabric: it.fabric,
            color: it.color,
            design_notes: it.design_notes,
          })),
      },
      {
        onSuccess: () => {
          toast.success("Order created");
          onClose();
        },
        onError: (err: unknown) =>
          toast.error(err instanceof Error ? err.message : "Failed"),
      }
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        className="absolute inset-0 bg-ink/20 backdrop-blur-sm"
        onClick={onClose}
      />
      <form
        onSubmit={submit}
        className="relative w-full max-w-xl h-full bg-white shadow-glow-lg overflow-y-auto"
      >
        <div className="sticky top-0 bg-white border-b border-lavender-100 px-7 py-5 flex items-center justify-between z-10">
          <h2 className="text-xl font-semibold">New order</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-ink-soft hover:bg-lavender-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-7 py-6 space-y-6">
          <div>
            <label className="label">Customer</label>

            {selectedCustomer ? (
              <div className="flex items-center justify-between gap-3 px-3.5 py-3 rounded-xl bg-gradient-to-r from-lavender-100 to-lavender-50 border-2 border-lavender-300 shadow-soft">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-lavender-400 to-lavender-600 flex items-center justify-center text-white text-sm font-semibold shadow-soft flex-shrink-0">
                    {selectedCustomer.full_name.slice(0, 1).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-ink truncate">
                      {selectedCustomer.full_name}
                    </div>
                    <div className="text-xs text-ink-soft truncate">
                      {selectedCustomer.phone}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setCustomerId("")}
                  className="text-xs font-medium text-lavender-700 hover:text-lavender-900 flex-shrink-0"
                >
                  Change
                </button>
              </div>
            ) : (
              <>
                <input
                  className="input mb-2"
                  placeholder="Search by name or phone…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <div className="max-h-[200px] overflow-y-auto border border-lavender-100 rounded-xl divide-y divide-lavender-100">
                  {customersQ.data?.results.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        setCustomerId(c.id);
                        setSearch("");
                      }}
                      className="w-full text-left px-3 py-2.5 text-sm hover:bg-lavender-50 active:bg-lavender-100 transition-colors flex items-center justify-between gap-3"
                    >
                      <span className="font-medium text-ink truncate">
                        {c.full_name}
                      </span>
                      <span className="text-xs text-ink-soft flex-shrink-0">
                        {c.phone}
                      </span>
                    </button>
                  ))}
                  {customersQ.data?.results.length === 0 && (
                    <div className="text-xs text-ink-soft text-center py-4">
                      No matches.
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Due date</label>
              <input
                type="date"
                className="input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">Currency</label>
              <select
                className="input"
                value={currency}
                onChange={(e) => setCurrency(e.target.value as Currency)}
              >
                <option value="EUR">EUR</option>
                <option value="COP">COP</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="label !mb-0">Items</label>
              <button
                type="button"
                onClick={() => setItems((prev) => [...prev, emptyItem()])}
                className="text-xs font-medium text-lavender-600 hover:text-lavender-700 inline-flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add item
              </button>
            </div>
            <div className="space-y-3">
              {items.map((it, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-lavender-100 p-4 bg-surface/40"
                >
                  <div className="grid grid-cols-12 gap-3">
                    <div className="col-span-5">
                      <label className="label">Garment</label>
                      <select
                        className="input"
                        value={it.garment_type}
                        onChange={(e) =>
                          updateItem(i, { garment_type: e.target.value })
                        }
                      >
                        {GARMENT_TYPES.map((g) => (
                          <option key={g.value} value={g.value}>
                            {g.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="col-span-3">
                      <label className="label">Qty</label>
                      <input
                        type="number"
                        min={1}
                        className="input"
                        value={it.quantity}
                        onChange={(e) =>
                          updateItem(i, { quantity: Number(e.target.value) })
                        }
                      />
                    </div>
                    <div className="col-span-4">
                      <label className="label">Unit price</label>
                      <input
                        className="input"
                        value={it.unit_price}
                        onChange={(e) =>
                          updateItem(i, { unit_price: e.target.value })
                        }
                      />
                    </div>
                    <div className="col-span-12">
                      <label className="label">Description</label>
                      <input
                        className="input"
                        value={it.description}
                        onChange={(e) =>
                          updateItem(i, { description: e.target.value })
                        }
                        placeholder="What's being made?"
                      />
                    </div>
                    <div className="col-span-6">
                      <label className="label">Fabric</label>
                      <input
                        className="input"
                        value={it.fabric}
                        onChange={(e) => updateItem(i, { fabric: e.target.value })}
                      />
                    </div>
                    <div className="col-span-6">
                      <label className="label">Color</label>
                      <input
                        className="input"
                        value={it.color}
                        onChange={(e) => updateItem(i, { color: e.target.value })}
                      />
                    </div>
                    <div className="col-span-12">
                      <label className="label">Design notes</label>
                      <textarea
                        className="input min-h-[60px]"
                        value={it.design_notes}
                        onChange={(e) =>
                          updateItem(i, { design_notes: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() =>
                        setItems((prev) => prev.filter((_, j) => j !== i))
                      }
                      className="mt-3 inline-flex items-center gap-1 text-xs text-rose-600 hover:text-rose-700"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="label">Order notes</label>
            <textarea
              className="input min-h-[80px]"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        <div className="sticky bottom-0 bg-white border-t border-lavender-100 px-7 py-4 flex justify-end gap-3 z-10">
          <button type="button" onClick={onClose} className="btn btn-ghost">
            Cancel
          </button>
          <button
            type="submit"
            disabled={createOrder.isPending}
            className="btn btn-primary disabled:opacity-60"
          >
            {createOrder.isPending ? "Creating…" : "Create order"}
          </button>
        </div>
      </form>
    </div>
  );
}
