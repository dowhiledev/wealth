"use client";

export type Account = {
  id: number;
  name: string;
  type: "exchange" | "wallet";
  datasource?: string | null;
  external_id?: string | null;
  currency: string;
  created_at: string;
};

export type AccountIn = Omit<Account, "id" | "created_at">;

export type Tx = {
  id: number;
  ts: string;
  account_id: number;
  asset_symbol: string;
  side: "buy" | "sell" | "transfer_in" | "transfer_out" | "stake" | "reward" | "fee";
  qty: string | number;
  price_quote?: string | number | null;
  total_quote?: string | number | null;
  quote_ccy?: string | null;
  fee_qty?: string | number | null;
  fee_asset?: string | null;
  note?: string | null;
  tx_hash?: string | null;
  external_id?: string | null;
  datasource?: string | null;
  import_batch_id?: number | null;
  tags?: string | null;
};

export type TxIn = Omit<Tx, "id">;

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  accounts: {
    list: () => http<Account[]>(`/accounts`),
    create: (body: AccountIn) => http<Account>(`/accounts`, { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: AccountIn) => http<Account>(`/accounts/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    remove: (id: number) => http<{ ok: boolean }>(`/accounts/${id}`, { method: "DELETE" }),
  },
  tx: {
    list: (params?: { account_id?: number; asset?: string; limit?: number; offset?: number }) => {
      const q = new URLSearchParams();
      if (params?.account_id) q.set("account_id", String(params.account_id));
      if (params?.asset) q.set("asset", params.asset);
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      const qs = q.toString();
      return http<Tx[]>(`/transactions${qs ? `?${qs}` : ""}`);
    },
    create: (body: TxIn) => http<Tx>(`/transactions`, { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: TxIn) => http<Tx>(`/transactions/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    remove: (id: number) => http<{ ok: boolean }>(`/transactions/${id}`, { method: "DELETE" }),
  },
};

