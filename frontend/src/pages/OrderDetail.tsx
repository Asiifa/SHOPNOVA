import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, inr } from "@/services/api";
import { Card } from "@/components/ui";
import type { Order, OrderItem } from "@/types";

export function OrderDetailPage() {
  const { id } = useParams();
  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ["order", id],
    queryFn: () => api.get<Order>(`/api/orders/${id}`),
    enabled: Boolean(id),
  });

  if (isLoading) return <div className="container-sn py-16">Loading order…</div>;
  if (!order) return <div className="container-sn py-16">Order not found.</div>;

  return (
    <div className="container-sn py-10">
      <h2 className="text-2xl font-bold text-navy mb-8">Order {order.order_number}</h2>
      <Card className="p-8 mb-8">
        <div className="grid gap-4 lg:grid-cols-3 mb-6">
          <div>
            <p className="text-xs text-mist">Order number</p>
            <p className="font-semibold">{order.order_number}</p>
          </div>
          <div>
            <p className="text-xs text-mist">Status</p>
            <p className="font-semibold text-navy">{order.order_status}</p>
          </div>
          <div>
            <p className="text-xs text-mist">Placed</p>
            <p className="font-semibold">{new Date(order.created_at).toLocaleDateString("en-IN")}</p>
          </div>
        </div>
        <h3 className="font-semibold text-navy mb-3">Items</h3>
        <div className="space-y-3">
          {order.items.map((item: OrderItem) => (
            <div key={item.id} className="flex gap-4 text-sm border-b pb-3">
              <div className="w-24 text-mist">{item.quantity}×</div>
              <div className="flex-1">{item.product_name}</div>
              <div className="text-right font-semibold">{inr(item.line_total)}</div>
            </div>
          ))}
          <div className="mt-4 pt-3 border-t border-navy/10 flex justify-between text-sm font-semibold">
            Total <span>{inr(order.total_amount)}</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
