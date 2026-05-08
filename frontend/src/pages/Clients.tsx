import { useState } from "react";
import { useForm } from "react-hook-form";
import { Mail, MapPin, Phone, Plus, Search, Trash2, UserPlus } from "lucide-react";
import toast from "react-hot-toast";

import {
  useCreateCustomer,
  useCustomers,
  useDeleteCustomer,
} from "../lib/queries";
import ConfirmDialog from "../components/ConfirmDialog";
import type { Customer } from "../lib/types";

interface FormValues {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  address: string;
  notes: string;
}

export default function Clients() {
  const [search, setSearch] = useState("");
  const [pendingDelete, setPendingDelete] = useState<Customer | null>(null);
  const customers = useCustomers(search);
  const create = useCreateCustomer();
  const del = useDeleteCustomer();
  const { register, handleSubmit, reset, formState } = useForm<FormValues>({
    defaultValues: {
      first_name: "",
      last_name: "",
      phone: "",
      email: "",
      address: "",
      notes: "",
    },
  });

  const onSubmit = (values: FormValues) => {
    create.mutate(values, {
      onSuccess: (c) => {
        toast.success(`Saved ${c.full_name}`);
        reset();
      },
      onError: (err: unknown) => {
        const detail = err instanceof Error ? err.message : "Failed";
        toast.error(detail);
      },
    });
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Clients</h1>
        <p className="text-ink-soft mt-1">
          Add a new client or browse the directory.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_420px] gap-6">
        {/* Directory */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold">Directory</h2>
              <p className="text-sm text-ink-soft mt-0.5">
                {customers.data?.count ?? 0} clients on file.
              </p>
            </div>
          </div>

          <div className="relative mb-5">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-ink-soft" />
            <input
              className="input pl-10"
              placeholder="Search by name, phone, email…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {customers.isLoading ? (
            <div className="text-ink-soft text-sm">Loading…</div>
          ) : customers.data?.results.length === 0 ? (
            <div className="text-sm text-ink-soft py-10 text-center border-2 border-dashed border-lavender-100 rounded-xl">
              No clients match your search.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {customers.data?.results.map((c) => (
                <div
                  key={c.id}
                  className="group card card-hover p-4 flex flex-col gap-1.5 relative"
                >
                  <button
                    type="button"
                    onClick={() => setPendingDelete(c)}
                    className="absolute top-2 right-2 w-7 h-7 rounded-lg flex items-center justify-center text-ink-soft opacity-0 group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-600 transition-all duration-150"
                    title={
                      c.order_count > 0
                        ? "Has orders — cannot delete"
                        : "Delete client"
                    }
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <div className="flex items-start justify-between pr-7">
                    <div className="text-sm font-semibold text-ink">
                      {c.full_name}
                    </div>
                    <span className="pill bg-lavender-50 text-lavender-700 ring-1 ring-lavender-200">
                      {c.order_count} {c.order_count === 1 ? "order" : "orders"}
                    </span>
                  </div>
                  <div className="text-xs text-ink-soft inline-flex items-center gap-1.5">
                    <Phone className="w-3 h-3" />
                    {c.phone}
                  </div>
                  {c.email && (
                    <div className="text-xs text-ink-soft inline-flex items-center gap-1.5">
                      <Mail className="w-3 h-3" />
                      {c.email}
                    </div>
                  )}
                  {c.address && (
                    <div className="text-xs text-ink-soft inline-flex items-start gap-1.5">
                      <MapPin className="w-3 h-3 mt-0.5 flex-shrink-0" />
                      <span className="line-clamp-2">{c.address}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* New client form */}
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="card p-6 h-fit sticky top-6 space-y-4"
        >
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lavender-300 to-lavender-600 flex items-center justify-center shadow-glow">
              <UserPlus className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">New client</h2>
              <p className="text-xs text-ink-soft">
                All you need is a name and phone.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First name</label>
              <input
                className="input"
                {...register("first_name", { required: true })}
              />
            </div>
            <div>
              <label className="label">Last name</label>
              <input
                className="input"
                {...register("last_name", { required: true })}
              />
            </div>
          </div>

          <div>
            <label className="label">Phone</label>
            <input
              className="input"
              placeholder="+34 …"
              {...register("phone", { required: true })}
            />
          </div>

          <div>
            <label className="label">Email</label>
            <input className="input" type="email" {...register("email")} />
          </div>

          <div>
            <label className="label">Address</label>
            <textarea
              className="input min-h-[60px]"
              {...register("address")}
            />
          </div>

          <div>
            <label className="label">Notes</label>
            <textarea
              className="input min-h-[60px]"
              placeholder="Preferences, allergies…"
              {...register("notes")}
            />
          </div>

          <button
            type="submit"
            disabled={create.isPending || formState.isSubmitting}
            className="btn btn-primary w-full disabled:opacity-60"
          >
            <Plus className="w-4 h-4" />
            {create.isPending ? "Saving…" : "Save client"}
          </button>
        </form>
      </div>

      <ConfirmDialog
        open={pendingDelete != null}
        title="Delete this client?"
        message={
          pendingDelete
            ? pendingDelete.order_count > 0
              ? `${pendingDelete.full_name} has ${pendingDelete.order_count} order(s). The server will refuse the delete — remove the orders first.`
              : `${pendingDelete.full_name} will be permanently removed from the directory.`
            : ""
        }
        confirmLabel="Delete client"
        destructive
        loading={del.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!pendingDelete) return;
          del.mutate(pendingDelete.id, {
            onSuccess: () => {
              toast.success("Client deleted");
              setPendingDelete(null);
            },
            onError: (err: unknown) => {
              toast.error(err instanceof Error ? err.message : "Delete failed");
              setPendingDelete(null);
            },
          });
        }}
      />
    </div>
  );
}
