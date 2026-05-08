export type Currency = "EUR" | "COP" | "USD";

export type OrderStatus =
  | "PENDING"
  | "IN_PRODUCTION"
  | "READY"
  | "DELIVERED"
  | "CANCELLED";

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: string | null;
  is_owner_or_manager: boolean;
}

export interface Customer {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  email: string;
  address: string;
  notes: string;
  created_at: string;
  updated_at: string;
  order_count: number;
}

export interface CustomerSlim {
  id: number;
  full_name: string;
  phone: string;
}

export interface OrderListRow {
  id: number;
  customer_name: string;
  order_date: string;
  due_date: string;
  status: OrderStatus;
  status_label: string;
  currency: Currency;
  total_price: string;
  item_count: number;
  notes: string;
}

export interface OrderItem {
  id: number;
  garment_type: string;
  garment_label: string;
  description: string;
  fabric: string;
  color: string;
  quantity: number;
  unit_price: string;
  design_notes: string;
  position: number;
}

export interface Order {
  id: number;
  customer: CustomerSlim;
  order_date: string;
  due_date: string;
  status: OrderStatus;
  status_label: string;
  currency: Currency;
  total_price: string;
  notes: string;
  items: OrderItem[];
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  orders_by_status: { status: OrderStatus; label: string; count: number }[];
  weekly_revenue: ({ week_start: string } & Record<Currency, number>)[];
  this_week_revenue: Partial<Record<Currency, number>>;
  upcoming_orders: OrderListRow[];
  active_count: number;
  overdue_count: number;
  pending_count: number;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const STATUS_ORDER: OrderStatus[] = [
  "PENDING",
  "IN_PRODUCTION",
  "READY",
  "DELIVERED",
  "CANCELLED",
];

export const STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING: "Pending",
  IN_PRODUCTION: "In production",
  READY: "Ready",
  DELIVERED: "Delivered",
  CANCELLED: "Cancelled",
};

export const STATUS_COLORS: Record<OrderStatus, { bg: string; text: string; ring: string }> = {
  PENDING: { bg: "bg-amber-50", text: "text-amber-700", ring: "ring-amber-200" },
  IN_PRODUCTION: { bg: "bg-lavender-50", text: "text-lavender-700", ring: "ring-lavender-200" },
  READY: { bg: "bg-emerald-50", text: "text-emerald-700", ring: "ring-emerald-200" },
  DELIVERED: { bg: "bg-slate-50", text: "text-slate-700", ring: "ring-slate-200" },
  CANCELLED: { bg: "bg-rose-50", text: "text-rose-700", ring: "ring-rose-200" },
};

export function formatMoney(amount: string | number, currency: Currency): string {
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  const symbol = currency === "EUR" ? "€" : currency === "COP" ? "$" : "$";
  return `${symbol}${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
}
