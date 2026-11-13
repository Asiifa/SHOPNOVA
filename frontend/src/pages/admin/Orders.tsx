import { useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Button, EmptyState, Input } from "@/components/ui";

type OrderRow = {
  id: string; order_number: string; customer_email: string | null; total_amount: number;
  order_status: string; payment_status: string; created_at: string;
};

export function AdminOrdersPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [statuses, setStatuses] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery<{ items: OrderRow[] }>({
    queryKey: ["admin/orders"],
    queryFn: () => api.get<{ items: OrderRow[] }>("/api/admin/orders?page=1&page_size=50"),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/api/admin/orders/${id}/status`, { order_status: status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin/orders"] });
      toast("Order status updated");
    },
    onError: (e: any) => toast(e.message || "Update failed"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;
  const items: OrderRow[] = (data?.items ?? []).map((o: any) => o);

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">Orders</h1>
      {!items.length ? (
        <EmptyState title="No orders" />
      ) : (
        <div className="overflow-x-auto border border-navy/10 rounded-2xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-mist">
                <th className="text-left p-3">Order number</th>
                <th className="text-left p-3">Customer</th>
                <th className="text-left p-3">Total (₹)</th>
                <th className="text-left p-3">Payment</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Placed</th>
                <th className="text-left p-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((o) => (
                <tr key={o.id} className="border-b last:border-0">
                  <td className="p-3 font-medium">{o.order_number}</td>
                  <td className="p-3 text-mist">{o.customer_email || "—"}</td>
                  <td className="p-3">{o.total_amount}</td>
                  <td className="p-3 text-mist">{o.payment_status}</td>
                  <td className="p-3">
                    {statuses[o.id] ? (
                      <Input value={statuses[o.id]} onChange={(e) => setStatuses({ ...statuses, [o.id]: e.target.value })} className="w-24 text-xs" />
                    ) : (
                      <select
                        value={o.order_status}
                        onChange={(e) => setStatuses({ ...statuses, [o.id]: e.target.value })}
                        className="input w-auto text-xs bg-transparent border-0 p-0"
                      >
                        {["PLACED", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"].map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="p-3 text-mist text-xs">{new Date(o.created_at).toLocaleDateString("en-IN")}</td>
                  <td className="p-3">
                    <Button
                      className="px-3 text-xs"
                      onClick={() => updateStatus.mutate({ id: o.id, status: statuses[o.id] || o.order_status })}
                      disabled={updateStatus.isPending}
                    >
                      Save
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
