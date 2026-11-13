import { useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Button, Input, EmptyState, Badge } from "@/components/ui";

type ProductRow = {
  id: string; name: string; slug: string; sku: string; brand: string; price: number;
  discount_price: number | null; city: string; image_url: string; is_active: boolean;
  available_quantity: number; category_name: string | null;
};

export function AdminProductsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<ProductRow> | null>(null);

  const { data, isLoading } = useQuery<{ items: ProductRow[] }>({
    queryKey: ["admin/products"],
    queryFn: () => api.get<{ items: ProductRow[] }>("/api/products?page=1&page_size=100"),
  });

  async function load() {
    await api.get<{ items: ProductRow[] }>("/api/products?page=1&page_size=100");
  }

  const updateStock = useMutation({
    mutationFn: ({ id, qty }: { id: string; qty: number }) =>
      api.patch(`/api/inventory/${id}`, { available_quantity: qty }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin/products"] });
      load();
      toast("Stock updated");
    },
    onError: (e: any) => toast(e.message || "Stock update failed"),
  });

  const deactivate = useMutation({
    mutationFn: (id: string) => api.delete(`/api/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin/products"] });
      load();
      toast("Product deactivated");
    },
    onError: (e: any) => toast(e.message || "Deactivate failed"),
  });

  if (isLoading) return <div className="p-10">Loading…</div>;
  load();

  return (
    <div className="p-6 md:p-10">
      <div className="flex items-end justify-between mb-6">
        <h1 className="text-2xl font-bold text-navy">Products</h1>
      </div>
      {!data || data.items.length === 0 ? (
        <EmptyState title="No products found" />
      ) : (
        <div className="overflow-x-auto border border-navy/10 rounded-2xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-mist">
                <th className="text-left p-3">Product</th>
                <th className="text-left p-3">SKU</th>
                <th className="text-left p-3">Category</th>
                <th className="text-left p-3">Price (₹)</th>
                <th className="text-left p-3">Stock</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p) => (
                <tr key={p.id} className="border-b last:border-0">
                  <td className="p-3">{p.name}</td>
                  <td className="p-3 text-mist">{p.sku}</td>
                  <td className="p-3 text-mist">{p.category_name || "—"}</td>
                  <td className="p-3 font-medium">{p.discount_price ?? p.price}</td>
                  <td className="p-3">
                    {editing === p.id ? (
                      <Input
                        type="number"
                        min="0"
                        value={draft?.available_quantity ?? p.available_quantity}
                        onChange={(e) => setDraft({ ...(draft || {}), available_quantity: Number(e.target.value) })}
                        className="w-20"
                      />
                    ) : (
                      p.available_quantity
                    )}
                  </td>
                  <td className="p-3">
                    <Badge variant={p.available_quantity === 0 ? "danger" : "ok"}>
                      {p.available_quantity > 0 ? "In stock" : "Out of stock"}
                    </Badge>
                  </td>
                  <td className="p-3">
                    {editing === p.id ? (
                      <div className="flex gap-2">
                        <Button className="px-3" onClick={() => updateStock.mutate({ id: p.id, qty: draft?.available_quantity ?? 0 })} disabled={updateStock.isPending}>Save</Button>
                        <Button className="px-3" onClick={() => { setEditing(null); setDraft(null); }}>Cancel</Button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <Button className="px-3" onClick={() => { setEditing(p.id); setDraft({ ...p, available_quantity: p.available_quantity }); }}>Edit stock</Button>
                        <Button className="px-3" onClick={() => deactivate.mutate(p.id)} disabled={deactivate.isPending}>Deactivate</Button>
                      </div>
                    )}
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
