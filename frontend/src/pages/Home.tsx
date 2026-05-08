import { useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Cell,
  CartesianGrid,
} from "recharts";
import {
  AlertCircle,
  Briefcase,
  Calendar,
  Clock,
  TrendingUp,
} from "lucide-react";
import { format, parseISO } from "date-fns";

import { useDashboard } from "../lib/queries";
import StatCard from "../components/StatCard";
import OrderCard from "../components/OrderCard";
import { formatMoney } from "../lib/types";
import type { Currency } from "../lib/types";

const STAGE_COLORS = ["#fcd34d", "#a98aff", "#34d399", "#94a3b8", "#fb7185"];

export default function Home() {
  const { data, isLoading, isError } = useDashboard();
  const [currency, setCurrency] = useState<Currency>("EUR");

  const chartData = useMemo(
    () => data?.orders_by_status.map((r) => ({ name: r.label, count: r.count })) ?? [],
    [data]
  );

  const weeklyChart = useMemo(
    () =>
      data?.weekly_revenue.map((w) => ({
        week: format(parseISO(w.week_start), "MMM d"),
        value: w[currency],
      })) ?? [],
    [data, currency]
  );

  if (isLoading) {
    return <div className="text-ink-soft">Loading dashboard…</div>;
  }
  if (isError || !data) {
    return <div className="text-rose-600">Failed to load dashboard.</div>;
  }

  const thisWeek = data.this_week_revenue[currency] ?? 0;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Home</h1>
        <p className="text-ink-soft mt-1">
          {format(new Date(), "EEEE, MMMM d, yyyy")}
        </p>
      </header>

      {/* Stat cards row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Active orders"
          value={data.active_count}
          hint="Not delivered or cancelled"
          icon={Briefcase}
        />
        <StatCard
          label="Pending"
          value={data.pending_count}
          hint="Waiting to start production"
          icon={Clock}
          accent="warning"
        />
        <StatCard
          label="Overdue"
          value={data.overdue_count}
          hint="Past due date, still open"
          icon={AlertCircle}
          accent={data.overdue_count > 0 ? "danger" : "default"}
        />
        <div className="card card-hover p-6 relative overflow-hidden">
          <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-gradient-to-br from-lavender-300 to-lavender-600 opacity-10 blur-2xl" />
          <div className="flex items-start justify-between relative">
            <div className="flex-1">
              <div className="text-xs font-semibold text-ink-soft uppercase tracking-wide">
                This week
              </div>
              <div className="text-3xl font-semibold text-ink mt-2">
                {formatMoney(thisWeek, currency)}
              </div>
              <div className="flex gap-1 mt-2.5">
                {(["EUR", "COP", "USD"] as Currency[]).map((c) => (
                  <button
                    key={c}
                    onClick={() => setCurrency(c)}
                    className={[
                      "px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors",
                      currency === c
                        ? "bg-lavender-100 text-lavender-700"
                        : "text-ink-soft hover:bg-lavender-50",
                    ].join(" ")}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-lavender-300 to-lavender-600 flex items-center justify-center shadow-soft">
              <TrendingUp className="w-5 h-5 text-white" strokeWidth={2.2} />
            </div>
          </div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-lg font-semibold">Orders by stage</h2>
            <span className="text-xs text-ink-soft">All time</span>
          </div>
          <p className="text-sm text-ink-soft mb-4">
            Distribution across the production pipeline.
          </p>
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ebe2ff" horizontal={false} />
                <XAxis type="number" allowDecimals={false} stroke="#5b5670" fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#5b5670"
                  fontSize={12}
                  width={110}
                />
                <Tooltip
                  cursor={{ fill: "rgba(139,109,240,0.06)" }}
                  contentStyle={{
                    background: "white",
                    border: "1px solid #ebe2ff",
                    borderRadius: 12,
                    boxShadow: "0 8px 24px rgba(26,21,48,0.08)",
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 6, 6]}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={STAGE_COLORS[i % STAGE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-lg font-semibold">Weekly revenue</h2>
            <div className="flex gap-1">
              {(["EUR", "COP", "USD"] as Currency[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setCurrency(c)}
                  className={[
                    "px-2 py-0.5 rounded-md text-[11px] font-medium transition-colors",
                    currency === c
                      ? "bg-lavender-100 text-lavender-700"
                      : "text-ink-soft hover:bg-lavender-50",
                  ].join(" ")}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
          <p className="text-sm text-ink-soft mb-4">Last 8 weeks · delivered orders.</p>
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyChart} margin={{ left: 10, right: 10 }}>
                <defs>
                  <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a98aff" />
                    <stop offset="100%" stopColor="#5d3fbf" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ebe2ff" vertical={false} />
                <XAxis dataKey="week" stroke="#5b5670" fontSize={12} />
                <YAxis stroke="#5b5670" fontSize={12} />
                <Tooltip
                  cursor={{ fill: "rgba(139,109,240,0.06)" }}
                  contentStyle={{
                    background: "white",
                    border: "1px solid #ebe2ff",
                    borderRadius: 12,
                    boxShadow: "0 8px 24px rgba(26,21,48,0.08)",
                  }}
                  formatter={(v: number) => formatMoney(v, currency)}
                />
                <Bar dataKey="value" fill="url(#barGrad)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Upcoming orders */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">Upcoming orders</h2>
            <p className="text-sm text-ink-soft mt-0.5">
              Next 10 by due date.
            </p>
          </div>
          <Calendar className="w-5 h-5 text-lavender-500" />
        </div>
        {data.upcoming_orders.length === 0 ? (
          <div className="text-sm text-ink-soft py-8 text-center">
            Nothing on the horizon — the workshop's clear.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.upcoming_orders.map((o) => (
              <OrderCard key={o.id} order={o} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
