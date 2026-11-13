import { useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Button, Input, EmptyState } from "@/components/ui";

type InvRow = { product_id: string; name: string; sku: string; available_quantity: number; reserved_quantity: number };

export function AdminInventoryPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [edits, setEdits] = useState<Record<string, number>>({});

  const { data, isLoading } = useQuery<InvRow[]>({
    queryKey: ["admin/inventory"],
    queryFn: () => api.get<InvRow[]>("/api/inventory"),
  });

  const adjust = useMutation({
    mutationFn: ({ id, qty }: { id: string; qty: number }) =>
      api.patch(`/api/inventory/${id}`, { available_quantity: qty }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin/inventory"] });
      toast("Inventory adjusted");
    },
    onError: (e: any) => toast(e.message || "Adjustment failed"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;
  const items: InvRow[] = data ?? [];

  return (
    <div className="p-6 md:p-10">
      <h1 className="text-2xl font-bold text-navy mb-6">Inventory</h1>
      {!items.length ? (
        <EmptyState title="No inventory records" />
      ) : (
        <div className="overflow-x-auto border border-navy/10 rounded-2xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-mist">
                <th className="text-left p-3">Product</th>
                <th className="text-left p-3">SKU</th>
                <th className="text-left p-3">Available</th>
                <th className="text-left p-3">Reserved</th>
                <th className="text-left p-3">Adjust</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.product_id} className="border-b last:border-0">
                  <td className="p-3">{i.name}</td>
                  <td className="p-3 text-mist">{i.sku}</td>
                  <td className="p-3 font-medium">{i.available_quantity}</td>
                  <td className="p-3 text-mist">{i.reserved_quantity}</td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        min="0"
                        value={edits[i.product_id] ?? i.available_quantity}
                        onChange={(e) => setEdits({ ...edits, [i.product_id]: Number(e.target.value) || 0 })}
                        className="w-24"
                      />
                      <Button
                        className="px-3 text-xs"
                        onClick={() => adjust.mutate({ id: i.product_id, qty: edits[i.product_id] ?? i.available_quantity })}
                        disabled={adjust.isPending}
                      >
                        Save
                      </Button>
                    </div>
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
