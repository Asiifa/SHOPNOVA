import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import type { Category, Product } from "../types";
import { ProductCard } from "../components/ProductCard";

export function ShopPage() {
  const [params, setParams] = useSearchParams();
  const category = params.get("category") || "";
  const sort = params.get("sort") || "newest";
  const page = Number(params.get("page") || "1");
  const products = useQuery({
    queryKey: ["shop", category, sort, page],
    queryFn: () => {
      const q = new URLSearchParams({ sort, page: String(page), page_size: "12" });
      if (category) q.set("category", category);
      return api.get<{ items: Product[]; total: number }>(`/api/products?${q}`);
    },
  });
  const categories = useQuery({ queryKey: ["categories"], queryFn: () => api.get<Category[]>("/api/categories") });

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params);
    Object.entries(next).forEach(([k, v]) => (v ? merged.set(k, v) : merged.delete(k)));
    if (!next.page) merged.set("page", "1");
    setParams(merged);
  }

  return (
    <main className="container-sn py-10">
      <h1 className="text-3xl font-bold text-navy">Shop</h1>
      <div className="mt-6 flex flex-wrap gap-3">
        <select className="input w-auto" value={category} onChange={(e) => update({ category: e.target.value })}>
          <option value="">All categories</option>
          {(categories.data ?? []).map((c) => (
            <option key={c.id} value={c.slug}>{c.name}</option>
          ))}
        </select>
        <select className="input w-auto" value={sort} onChange={(e) => update({ sort: e.target.value })}>
          <option value="newest">Newest</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="popularity">Popularity</option>
        </select>
      </div>
      {products.isLoading ? <p className="mt-10 text-mist">Loading catalogue…</p> : null}
      {products.isError ? (
        <p className="mt-10 text-danger">
          Unable to load products. {products.error instanceof Error ? products.error.message : "Is the API running?"}
        </p>
      ) : null}
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {(products.data?.items ?? []).map((p) => <ProductCard key={p.id} product={p} />)}
      </div>
      <div className="mt-10 flex justify-center gap-3">
        <button className="btn-ghost" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>Previous</button>
        <button className="btn-ghost" onClick={() => update({ page: String(page + 1) })}>Next</button>
      </div>
    </main>
  );
}
