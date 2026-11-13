import { useQuery } from "@tanstack/react-query";
import { api, inr } from "@/services/api";
import { Card, EmptyState } from "@/components/ui";
import type { PaginatedOrders } from "@/types";

export function MyOrdersPage() {
  const { data: page } = useQuery({
    queryKey: ["orders"],
    queryFn: () => api.get<PaginatedOrders>("/api/orders?page=1&page_size=20"),
  });

  return (
    <div className="container-sn py-10">
      <h2 className="text-2xl font-bold text-navy mb-8">My orders</h2>
      <div className="space-y-5">
        {(page?.items ?? []).map((order: any) => (
          <Card key={order.id} className="p-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-semibold text-navy">{order.order_number}</p>
                <p className="text-xs text-mist">{new Date(order.created_at).toLocaleDateString("en-IN")}</p>
              </div>
              <span className="text-xs font-semibold text-navy/80">{order.order_status}</span>
            </div>
            <div className="flex justify-between text-sm mb-3">
              <span className="text-mist">Total</span>
              <span className="font-medium">{inr(order.total_amount)}</span>
            </div>
            <a href={`/orders/${order.id}`} className="text-sm text-coral hover:underline">
              View order →
            </a>
          </Card>
        ))}
      </div>
      {(page?.items?.length ?? 0) === 0 && (
        <EmptyState title="No orders yet" description="Place your first order from the shop." />
      )}
    </div>
  );
}
