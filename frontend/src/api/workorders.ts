import { api } from "./client";
import type { WorkOrder } from "@/types";

export const workOrdersApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<WorkOrder[]>("/workorders", { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<WorkOrder>(`/workorders/${id}`).then((r) => r.data),

  create: (payload: Partial<WorkOrder>) =>
    api.post<WorkOrder>("/workorders", payload).then((r) => r.data),

  update: (id: string, payload: Partial<WorkOrder>) =>
    api.patch<WorkOrder>(`/workorders/${id}`, payload).then((r) => r.data),
};
