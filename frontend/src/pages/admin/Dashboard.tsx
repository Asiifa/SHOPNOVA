import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card } from "@/components/ui";

type DashStats = {
  orders: number; customers: number; active_products: number; revenue_inr: number;
  unpublished_outbox: number; processed_events: number; low_stock_skus: number;
};

export function AdminDashboardPage() {
  const { data, isLoading } = useQuery<DashStats>({
    queryKey: ["admin/dashboard"],
    queryFn: () => api.get<DashStats>("/api/admin/dashboard"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;
  if (!data) return <div className="p-10">Unable to load dashboard.</div>;

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-8">Admin dashboard</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[["Orders", data.orders], ["Customers", data.customers], ["Active products", data.active_products], ["Revenue (₹)", data.revenue_inr ?? 0]].map(
          ([label, value]) => (
            <Card key={label} className="p-6">
              <p className="text-xs text-mist uppercase">{label}</p>
              <p className="mt-2 text-2xl font-bold text-navy">{typeof value === "number" ? value.toLocaleString("en-IN") : value}</p>
            </Card>
          ),
        )}
      </div>
      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        <Card className="p-6">
          <p className="text-xs text-mist uppercase">Unpublished outbox events</p>
          <p className="mt-2 text-2xl font-bold">{data.unpublished_outbox ?? 0}</p>
        </Card>
        <Card className="p-6">
          <p className="text-xs text-mist uppercase">Processed events</p>
          <p className="mt-2 text-2xl font-bold">{data.processed_events ?? 0}</p>
        </Card>
        <Card className="p-6">
          <p className="text-xs text-mist uppercase">Low-stock products</p>
          <p className="mt-2 text-2xl font-bold text-danger">{data.low_stock_skus ?? 0}</p>
        </Card>
      </div>
    </div>
  );
}
