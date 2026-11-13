import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, inr } from "../services/api";
import { Link } from "react-router-dom";

type Hit = {
  id: string;
  name: string;
  brand: string;
  price: number;
  image_url: string;
  in_stock: boolean;
  city: string;
  category_slug?: string;
};

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const [min, setMin] = useState(params.get("min_price") || "");
  const [max, setMax] = useState(params.get("max_price") || "");
  const [category, setCategory] = useState(params.get("category") || "");
  const [sort, setSort] = useState(params.get("sort") || "relevance");

  const result = useQuery({
    queryKey: ["search", params.toString()],
    queryFn: () => api.get<{ items: Hit[]; total: number; engine: string }>(`/api/search?${params}`),
    enabled: true,
  });

  function apply(e: FormEvent) {
    e.preventDefault();
    const next = new URLSearchParams();
    if (q) next.set("q", q);
    if (min) next.set("min_price", min);
    if (max) next.set("max_price", max);
    if (category) next.set("category", category);
    next.set("sort", sort);
    setParams(next);
  }

  return (
    <main className="container-sn py-10">
      <h1 className="text-3xl font-bold text-navy">Search</h1>
      <p className="mt-2 text-sm text-mist">
        Results come from Aiven OpenSearch{result.data ? ` · engine=${result.data.engine}` : ""}. Try “bluetoth hedphones”.
      </p>
      <form onSubmit={apply} className="mt-6 grid gap-3 md:grid-cols-5">
        <input className="input" placeholder="Min price" value={min} onChange={(e) => setMin(e.target.value)} />
        <input className="input" placeholder="Max price" value={max} onChange={(e) => setMax(e.target.value)} />
        <input className="input" placeholder="Category slug" value={category} onChange={(e) => setCategory(e.target.value)} />
        <select className="input" value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="relevance">Relevance</option>
          <option value="price_asc">Price ascending</option>
          <option value="price_desc">Price descending</option>
          <option value="newest">Newest</option>
          <option value="popularity">Popularity</option>
        </select>
        <button className="btn-primary">Filter</button>
      </form>
      {result.isError ? (
        <p className="mt-8 text-danger">
          Search is unavailable until OpenSearch is configured privately and the index is populated.
        </p>
      ) : null}
      {!result.isLoading && result.data?.total === 0 ? <p className="mt-8 text-mist">No matching products.</p> : null}
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {(result.data?.items ?? []).map((item) => (
          <Link key={item.id} to={`/product/${item.id}`} className="card overflow-hidden">
            <img src={item.image_url} alt="" className="h-52 w-full object-cover" />
            <div className="p-4">
              <p className="text-xs text-mist">{item.brand}</p>
              <h3 className="font-semibold text-navy">{item.name}</h3>
              <p className="mt-1">{inr(item.price)}</p>
              <p className="text-xs text-mist">{item.in_stock ? "In stock" : "Out of stock"} · {item.city}</p>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
