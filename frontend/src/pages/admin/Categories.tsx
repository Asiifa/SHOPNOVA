import { useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Card, Button, Input, EmptyState } from "@/components/ui";
import type { Category } from "@/types";

export function AdminCategoriesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  const { data, isLoading, refetch } = useQuery<Category[]>({
    queryKey: ["admin/categories"],
    queryFn: () => api.get<Category[]>("/api/categories"),
  });

  const create = useMutation({
    mutationFn: () => api.post("/api/categories", { name, slug }),
    onSuccess: () => {
      setName(""); setSlug("");
      queryClient.invalidateQueries({ queryKey: ["admin/categories"] });
      refetch();
      toast("Category created");
    },
    onError: (e: any) => toast(e.message || "Create failed"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">Categories</h1>
      <Card className="p-6 mb-8 w-full max-w-md">
        <div className="grid gap-3 sm:grid-cols-2 items-end">
          <Input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <Input placeholder="Slug" value={slug} onChange={(e) => setSlug(e.target.value)} />
          <Button className="w-full" onClick={() => create.mutate()} disabled={create.isPending || !name || !slug}>
            Create
          </Button>
        </div>
      </Card>
      {!data || data.length === 0 ? (
        <EmptyState title="No categories" />
      ) : (
        <div className="space-y-2">
          {data.map((c: any) => (
            <Card key={c.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold text-navy">{c.name}</p>
                <p className="text-xs text-mist">{c.slug}</p>
              </div>
              <span className="text-xs text-navy/80">{c.sort_order}</span>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
