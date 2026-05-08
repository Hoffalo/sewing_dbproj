import { AlertTriangle } from "lucide-react";

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  destructive = false,
  onConfirm,
  onCancel,
  loading = false,
}: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center px-6">
      <div
        className="absolute inset-0 bg-ink/30 backdrop-blur-sm"
        onClick={onCancel}
      />
      <div className="relative w-full max-w-md card p-6 shadow-glow-lg">
        <div className="flex items-start gap-4">
          <div
            className={[
              "w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0",
              destructive
                ? "bg-rose-50 text-rose-600"
                : "bg-lavender-50 text-lavender-600",
            ].join(" ")}
          >
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-ink">{title}</h3>
            <p className="text-sm text-ink-soft mt-1">{message}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="btn btn-ghost"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={[
              "btn disabled:opacity-60",
              destructive
                ? "bg-gradient-to-br from-rose-500 to-rose-600 text-white shadow-soft hover:shadow-glow active:scale-[0.98]"
                : "btn-primary",
            ].join(" ")}
          >
            {loading ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
