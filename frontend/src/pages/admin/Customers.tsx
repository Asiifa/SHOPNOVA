import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card, EmptyState } from "@/components/ui";
import type { User } from "@/types";

type CustomerRow = User & { is_active: boolean };

export function AdminCustomersPage() {
  const { data, isLoading } = useQuery<CustomerRow[]>({
    queryKey: ["admin/customers"],
    queryFn: () => api.get<CustomerRow[]>("/api/admin/customers"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;
  const customers: any[] = data ?? [];

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">Customers</h1>
      {!customers.length ? (
        <EmptyState title="No customers" />
      ) : (
        <div className="space-y-3">
          {customers.map((c) => (
            <Card key={c.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold text-navy">{c.full_name}</p>
                <p className="text-sm text-mist">{c.email}</p>
              </div>
              <span className={`text-xs font-semibold ${c.is_active ? "text-success" : "text-danger"}`}>
                {c.is_active ? "Active" : "Inactive"}
              </span>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
