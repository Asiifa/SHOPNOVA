import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, inr } from "@/services/api";
import { Card, EmptyState, Badge } from "@/components/ui";
import type { Order, OrderItem } from "@/types";

export function OrderConfirmationPage() {
  const { id } = useParams();
  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ["order", id],
    queryFn: () => api.get<Order>(`/api/orders/${id}`),
    enabled: Boolean(id),
  });

  if (isLoading) return <div className="container-sn py-16"><div className="mx-auto animate-pulse rounded-full bg-navy/5 w-24 h-24" /></div>;
  if (!order) return <div className="container-sn py-16"><EmptyState title="Order not found" /></div>;

  const statusBadge = (s: string) => {
    const map: Record<string, string> = {
      PLACED: "Placed — awaiting stock confirmation",
      CONFIRMED: "Confirmed",
      PACKED: "Packed",
      SHIPPED: "Shipped",
      DELIVERED: "Delivered",
      CANCELLED: "Cancelled",
    };
    return <Badge variant="ok">{map[s] || s}</Badge>;
  };

  return (
    <div className="container-sn py-12">
      <Card className="p-10 md:p-14">
        <div className="flex items-start justify-between md:flex-col md:items-start gap-4 mb-10">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-success">Order confirmed</p>
            <h1 className="mt-2 text-3xl font-bold text-navy">Thank you, {order.order_number}</h1>
            <p className="mt-2 text-mist">Your order has been received and is being processed.</p>
          </div>
          <div className="text-right">
            <div className="text-mist text-sm">Order placed</div>
            <div className="text-navy font-semibold">{new Date(order.created_at).toLocaleDateString("en-IN")}</div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-4 mb-10">
          <div className="col-span-4 lg:col-span-2">
            <h3 className="font-semibold text-navy mb-3">Customer</h3>
            <p className="text-mist text-sm">{order.customer?.full_name || "Guest"}</p>
            <p className="text-mist text-sm">{order.customer?.email || "-"}</p>
          </div>
          <div className="col-span-4 lg:col-span-2">
            <h3 className="font-semibold text-navy mb-3">Order number</h3>
            <p className="text-mist text-sm">{order.order_number}</p>
            <p className="text-mist text-sm">{order.payment_method}</p>
          </div>
        </div>

        <h3 className="font-semibold text-navy mb-4">Order status</h3>
        <div className="flex items-center gap-3 mb-10">
          {statusBadge(order.order_status)}
        </div>

        <h3 className="font-semibold text-navy mb-4">Items</h3>
        <div className="space-y-4 mb-10">
          {order.items.map((item: OrderItem) => (
            <div key={item.id} className="flex gap-4 text-sm">
              <div className="w-20 text-mist">{item.quantity}×</div>
              <div className="flex-1">{item.product_name} ({item.sku})</div>
              <div className="font-semibold">{inr(item.line_total)}</div>
            </div>
          ))}
          <div className="mt-4 pt-4 border-t border-navy/10 flex justify-between text-sm font-semibold">
            Total <span>{inr(order.total_amount)}</span>
          </div>
        </div>

        <div className="pt-6 border-t border-navy/10 text-sm text-mist">
          Track this order anytime in <a href="/orders" className="text-coral hover:underline">My Orders</a>.
        </div>
      </Card>
    </div>
  );
}
