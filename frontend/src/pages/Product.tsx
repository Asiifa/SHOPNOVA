import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, inr } from "../services/api";
import type { Product } from "../types";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { ProductCard } from "../components/ProductCard";

export function ProductPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [qty, setQty] = useState(1);
  const product = useQuery<Product>({
    queryKey: ["product", id],
    queryFn: () => api.get<Product>(`/api/products/${id}`),
    enabled: Boolean(id),
  });
  const related = useQuery<{ items: Product[] }>({
    queryKey: ["related", product.data?.category_slug],
    queryFn: () => api.get<{ items: Product[] }>(`/api/products?category=${product.data?.category_slug}&page_size=4`),
    enabled: Boolean(product.data?.category_slug),
  });

  async function addToCart(buyNow = false) {
    if (!user) {
      navigate("/login");
      return;
    }
    try {
      await api.post("/api/cart/items", { product_id: id, quantity: qty });
      await qc.invalidateQueries({ queryKey: ["cart"] });
      toast("Added to bag");
      if (buyNow) navigate("/checkout");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Unable to add");
    }
  }

  if (product.isLoading) return <p className="container-sn py-16 text-mist">Loading product…</p>;
  if (!product.data) return <p className="container-sn py-16 text-danger">Product not found.</p>;
  const p = product.data;
  const price = p.discount_price ?? p.price;

  return (
    <main className="container-sn py-10">
      <div className="grid gap-10 md:grid-cols-2">
        <div className="overflow-hidden rounded-3xl bg-white">
          <img src={p.images[0] || p.image_url || ""} alt={p.name} className="h-[520px] w-full object-cover" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-widest text-mist">{p.brand} · {p.city}</p>
          <h1 className="mt-2 text-3xl font-bold text-navy">{p.name}</h1>
          <p className="mt-3 text-2xl font-semibold">
            {inr(price)} {p.discount_price ? <span className="text-base text-mist line-through">{inr(p.price)}</span> : null}
          </p>
          <p className="mt-4 text-sm leading-6 text-mist">{p.description}</p>
          <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
            {Object.entries(p.specifications || {}).map(([k, v]) => (
              <div key={k} className="rounded-xl bg-white p-3">
                <dt className="text-mist">{k}</dt>
                <dd className="font-medium">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 text-sm">{p.available_quantity > 0 ? `${p.available_quantity} in stock` : "Out of stock"}</p>
          <div className="mt-4 flex items-center gap-3">
            <input className="input w-24" type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} />
            <button className="btn-primary" onClick={() => addToCart(false)} disabled={p.available_quantity < 1}>Add to cart</button>
            <button className="btn-accent" onClick={() => addToCart(true)} disabled={p.available_quantity < 1}>Buy now</button>
          </div>
        </div>
      </div>
      <h2 className="mt-16 text-2xl font-bold text-navy">Related</h2>
      <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {(related.data?.items ?? []).filter((x) => x.id !== p.id).map((item) => <ProductCard key={item.id} product={item} />)}
      </div>
    </main>
  );
}
