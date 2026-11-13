import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Button, Card } from "@/components/ui";

export function AdminSearchPage() {
  const [reindexing, setReindexing] = useState(false);
  const toast = useToast();
  const { data, isLoading } = useQuery<{ opensearch: { index: string; configured: boolean; verify_certs: boolean } }>({
    queryKey: ["admin/system-health"],
    queryFn: () => api.get<{ opensearch: { index: string; configured: boolean; verify_certs: boolean } }>("/api/admin/system-health"),
  });

  const trigger = async () => {
    setReindexing(true);
    try {
      await api.post("/api/admin/search/reindex");
      toast("Reindex queued");
    } catch (e: any) {
      toast(e.message || "Reindex failed");
    } finally {
      setReindexing(false);
    }
  };

  if (isLoading) return <div className="p-10">Loading…</div>;
  const os = (data?.opensearch ?? {}) as { index: string; configured: boolean; verify_certs: boolean };

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">Search indexing</h1>
      <Card className="p-8 w-full max-w-lg">
        <h2 className="font-semibold text-navy mb-3">OpenSearch</h2>
        <p className="text-sm text-mist mb-4">
          Index: <span className="font-mono text-xs">{os.index}</span>
        </p>
        <p className="text-sm text-mist">
          Configured: {os.configured ? "yes" : "no"} &nbsp;·&nbsp;
          Verify certs: {String(os.verify_certs)}
        </p>
        <div className="mt-6">
          <Button className="w-full" onClick={trigger} disabled={reindexing || !os.configured}>
            {reindexing ? "Reindexing…" : "Rebuild search index"}
          </Button>
          {!os.configured && <p className="mt-3 text-xs text-danger">OpenSearch credentials not configured.</p>}
        </div>
      </Card>
    </div>
  );
}
