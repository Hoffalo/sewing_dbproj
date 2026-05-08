import type { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  hint?: string;
  icon: LucideIcon;
  accent?: "default" | "warning" | "danger";
}

const accents = {
  default: "from-lavender-300 to-lavender-600",
  warning: "from-amber-300 to-amber-500",
  danger: "from-rose-300 to-rose-500",
};

export default function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  accent = "default",
}: Props) {
  return (
    <div className="card card-hover p-6 relative overflow-hidden">
      <div
        className={`absolute -top-10 -right-10 w-40 h-40 rounded-full bg-gradient-to-br ${accents[accent]} opacity-10 blur-2xl`}
      />
      <div className="flex items-start justify-between relative">
        <div className="flex-1">
          <div className="text-xs font-semibold text-ink-soft uppercase tracking-wide">
            {label}
          </div>
          <div className="text-3xl font-semibold text-ink mt-2">{value}</div>
          {hint && (
            <div className="text-xs text-ink-soft mt-1.5">{hint}</div>
          )}
        </div>
        <div
          className={`w-11 h-11 rounded-xl bg-gradient-to-br ${accents[accent]} flex items-center justify-center shadow-soft`}
        >
          <Icon className="w-5 h-5 text-white" strokeWidth={2.2} />
        </div>
      </div>
    </div>
  );
}
