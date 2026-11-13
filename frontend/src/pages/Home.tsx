import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { Category, Product } from "../types";
import { ProductCard } from "../components/ProductCard";

export function HomePage() {
  const categories = useQuery({ queryKey: ["categories"], queryFn: () => api.get<Category[]>("/api/categories") });
  const trending = useQuery({
    queryKey: ["trending"],
    queryFn: () => api.get<{ items: Product[] }>("/api/products?sort=popularity&page_size=8"),
  });
  const newest = useQuery({
    queryKey: ["newest"],
    queryFn: () => api.get<{ items: Product[] }>("/api/products?sort=newest&page_size=8"),
  });

  return (
    <main>
      <section className="container-sn grid items-center gap-10 py-12 md:grid-cols-2 md:py-20">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">India, thoughtfully stocked</p>
          <h1 className="mt-4 max-w-xl text-4xl font-extrabold leading-tight text-navy md:text-5xl">
            From neighbourhood shelves to your door.
          </h1>
          <p className="mt-5 max-w-lg text-mist">
            SHOPNOVA is built for retailers moving online without losing the care of a physical store — real inventory, real search, real orders.
          </p>
          <div className="mt-8 flex gap-3">
            <Link to="/shop" className="btn-primary">Browse the shop</Link>
            <Link to="/search?q=headphones" className="btn-ghost">Try product search</Link>
          </div>
        </div>
        <img
          src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1400&q=80"
          alt="Calm retail interior"
          className="h-[420px] w-full rounded-3xl object-cover"
        />
      </section>

      <section className="container-sn py-8">
        <h2 className="text-2xl font-bold text-navy">Featured categories</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(categories.data ?? []).map((c) => (
            <Link key={c.id} to={`/shop?category=${c.slug}`} className="card overflow-hidden">
              <img src={c.image_url || ""} alt="" className="h-40 w-full object-cover" />
              <div className="p-4">
                <h3 className="font-semibold text-navy">{c.name}</h3>
                <p className="mt-1 text-sm text-mist">{c.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="container-sn py-8">
        <div className="flex items-end justify-between">
          <h2 className="text-2xl font-bold text-navy">Trending</h2>
          <Link to="/shop?sort=popularity" className="text-sm text-coral">View all</Link>
        </div>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {(trending.data?.items ?? []).map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      </section>

      <section className="container-sn py-8">
        <h2 className="text-2xl font-bold text-navy">Best sellers & new arrivals</h2>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {(newest.data?.items ?? []).map((p) => <ProductCard key={p.id} product={p} />)}
        </div>
      </section>

      <section className="container-sn my-8 overflow-hidden rounded-3xl bg-navy p-10 text-white md:flex md:items-center md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-widest text-coral">Special offer</p>
          <h2 className="mt-2 text-3xl font-bold">Free shipping above ₹999</h2>
          <p className="mt-2 text-white/70">Cash on delivery, or a clearly labelled simulated card payment for this hackathon MVP.</p>
        </div>
        <Link to="/deals" className="btn-accent mt-6 md:mt-0">Shop deals</Link>
      </section>

      <section className="container-sn grid gap-6 py-10 md:grid-cols-3">
        {[
          ["Assured stock", "Inventory is reserved in PostgreSQL at checkout, not hoped for later."],
          ["Search that forgives typos", "OpenSearch ranks “bluetoth hedphones” as Bluetooth headphones."],
          ["Events you can audit", "Kafka carries committed order and product events to search and notifications."],
        ].map(([title, body]) => (
          <div key={title} className="card p-6">
            <h3 className="font-semibold text-navy">{title}</h3>
            <p className="mt-2 text-sm text-mist">{body}</p>
          </div>
        ))}
      </section>

      <section className="container-sn mb-16 rounded-3xl bg-white p-8 shadow-card md:flex md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-navy">Notes from the studio</h2>
          <p className="mt-2 text-sm text-mist">Seasonal drops, restocks and quiet offers. No spam.</p>
        </div>
        <form className="mt-4 flex gap-2 md:mt-0" onSubmit={(e) => e.preventDefault()}>
          <input className="input w-64" placeholder="Email address" />
          <button className="btn-primary" type="submit">Subscribe</button>
        </form>
      </section>
    </main>
  );
}
