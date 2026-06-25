import { api } from "./client";
import type { Asset } from "@/types";

export const assetsApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<Asset[]>("/assets", { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Asset>(`/assets/${id}`).then((r) => r.data),

  create: (payload: Partial<Asset>) =>
    api.post<Asset>("/assets", payload).then((r) => r.data),

  update: (id: string, payload: Partial<Asset>) =>
    api.patch<Asset>(`/assets/${id}`, payload).then((r) => r.data),

  getRUL: (id: string) =>
    api.get(`/assets/${id}/rul`).then((r) => r.data),

  lookupQR: (qr: string) =>
    api.get<Asset>(`/assets/qr/${qr}`).then((r) => r.data),
};
