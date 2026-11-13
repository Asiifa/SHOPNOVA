import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card } from "@/components/ui";

export function AdminEventsPage() {
  const { data, isLoading } = useQuery<{ outbox: any[]; processed: any[] }>({
    queryKey: ["admin/events"],
    queryFn: () => api.get<{ outbox: any[]; processed: any[] }>("/api/admin/events?limit=50"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;
  const outbox: any[] = (data?.outbox ?? []);
  const processed: any[] = (data?.processed ?? []);

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">Kafka events</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6 col-span-2 lg:col-span-1">
          <h2 className="font-semibold text-navy mb-4">Outbox (unpublished first)</h2>
          {!outbox.length ? <p className="text-mist text-sm">None</p> : (
            <div className="space-y-2">
              {outbox.map((e) => (
                <div key={e.event_id} className="text-xs border-b pb-2 last:border-0">
                  <div className="font-medium">{e.event_type}</div>
                  <div className="text-mist">{e.topic} · {e.published ? "published" : "pending"}</div>
                  {e.last_error && <div className="text-xs text-danger mt-1">{e.last_error}</div>}
                </div>
              ))}
            </div>
          )}
        </Card>
        <Card className="p-6 col-span-2 lg:col-span-1">
          <h2 className="font-semibold text-navy mb-4">Processed events (idempotency)</h2>
          {!processed.length ? <p className="text-mist text-sm">None</p> : (
            <div className="space-y-2">
              {processed.map((e) => (
                <div key={`${e.consumer_name}-${e.event_id}`} className="text-xs border-b pb-2 last:border-0">
                  <div className="font-medium">{e.event_type}</div>
                  <div className="text-mist">{e.consumer_name}</div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
