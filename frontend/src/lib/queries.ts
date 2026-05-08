import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { api } from "./api";
import type {
  Customer,
  DashboardData,
  Order,
  OrderListRow,
  OrderStatus,
  Paginated,
  User,
} from "./types";

// --- Auth ---------------------------------------------------------------
export const useMe = () =>
  useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const res = await api.get<{ user: User }>("/auth/me/");
      return res.user;
    },
    retry: false,
  });

export const useLogin = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (creds: { username: string; password: string }) =>
      api.post<{ user: User }>("/auth/login/", creds),
    onSuccess: (data) => qc.setQueryData(["me"], data.user),
  });
};

export const useLogout = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<void>("/auth/logout/"),
    onSuccess: () => {
      qc.setQueryData(["me"], null);
      qc.clear();
    },
  });
};

// --- Dashboard ---------------------------------------------------------
export const useDashboard = () =>
  useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardData>("/dashboard/"),
  });

// --- Orders ------------------------------------------------------------
export const useOrders = (status?: OrderStatus) =>
  useQuery({
    queryKey: ["orders", status ?? "all"],
    queryFn: () =>
      api.get<Paginated<OrderListRow>>("/orders/", { status, page_size: 100 }),
  });

export const useOrder = (id: number | null) =>
  useQuery({
    queryKey: ["orders", "detail", id],
    queryFn: () => api.get<Order>(`/orders/${id}/`),
    enabled: !!id,
  });

export const useMoveOrder = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: OrderStatus }) =>
      api.post<OrderListRow>(`/orders/${id}/move/`, { status }),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: ["orders"] });
      const snapshots = qc.getQueriesData<Paginated<OrderListRow>>({
        queryKey: ["orders"],
      });
      // Optimistic: update the cached list (status filter "all" specifically).
      qc.setQueryData<Paginated<OrderListRow>>(["orders", "all"], (old) =>
        old
          ? {
              ...old,
              results: old.results.map((o) =>
                o.id === id ? { ...o, status } : o
              ),
            }
          : old
      );
      return { snapshots };
    },
    onError: (_err, _vars, ctx) => {
      ctx?.snapshots.forEach(([key, value]) => qc.setQueryData(key, value));
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
};

export const useCreateOrder = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      customer_id: number;
      due_date: string;
      currency: string;
      notes?: string;
      items_input: {
        garment_type: string;
        description: string;
        quantity: number;
        unit_price: string;
        fabric?: string;
        color?: string;
        design_notes?: string;
      }[];
    }) => api.post<Order>("/orders/", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
};

export const useDeleteOrder = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/orders/${id}/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
};

// --- Customers ----------------------------------------------------------
export const useCustomers = (search?: string) =>
  useQuery({
    queryKey: ["customers", search ?? ""],
    queryFn: () =>
      api.get<Paginated<Customer>>("/customers/", { search, page_size: 100 }),
  });

export const useCreateCustomer = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      first_name: string;
      last_name: string;
      phone: string;
      email?: string;
      address?: string;
      notes?: string;
    }) => api.post<Customer>("/customers/", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["customers"] }),
  });
};

export const useDeleteCustomer = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/customers/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["customers"] }),
  });
};
