import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card } from "@/components/ui";

type Svc = { service?: string; configured?: boolean; index?: string };

export function AdminHealthPage() {
  const { data, isLoading } = useQuery<{ postgres: Svc; kafka: Svc; opensearch: Svc }>({
    queryKey: ["admin/health"],
    queryFn: () => api.get<{ postgres: Svc; kafka: Svc; opensearch: Svc }>("/api/admin/system-health"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">System health</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[["postgres", data?.postgres], ["kafka", data?.kafka], ["opensearch", data?.opensearch]].map(
          ([key, svc]: any) => (
            <Card key={key} className="p-6">
              <p className="text-xs text-mist uppercase">{key}</p>
              <p className="text-xs text-mist mb-3">{svc?.service || "-"}</p>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${svc?.configured ? "bg-success" : "bg-danger"}`}></span>
                <span className="text-sm font-medium">{svc?.configured ? "configured" : "not configured"}</span>
              </div>
              {svc?.index && <p className="mt-2 text-xs text-mist">Index: {svc.index}</p>}
            </Card>
          ),
        )}
      </div>
    </div>
  );
}
