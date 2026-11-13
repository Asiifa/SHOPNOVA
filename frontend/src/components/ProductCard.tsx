import { Link } from "react-router-dom";
import type { Product } from "../types";
import { inr } from "../services/api";
import { discountPercent } from "../utils/format";

export function ProductCard({ product }: { product: Product }) {
  const sale = product.discount_price ?? product.price;
  const off = discountPercent(product.price, product.discount_price);
  return (
    <Link to={`/product/${product.id}`} className="card group overflow-hidden">
      <div className="relative aspect-[4/5] overflow-hidden bg-[#efe8df]">
        <img src={product.image_url || ""} alt={product.name} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]" />
        {off ? <span className="absolute left-3 top-3 rounded-full bg-coral px-2 py-1 text-xs font-semibold text-white">{off}% off</span> : null}
      </div>
      <div className="space-y-1 p-4">
        <p className="text-xs uppercase tracking-wide text-mist">{product.brand}</p>
        <h3 className="line-clamp-2 text-sm font-semibold text-navy">{product.name}</h3>
        <div className="flex items-baseline gap-2">
          <span className="font-semibold">{inr(sale)}</span>
          {product.discount_price ? <span className="text-xs text-mist line-through">{inr(product.price)}</span> : null}
        </div>
        <p className="text-xs text-mist">{product.available_quantity > 0 ? "In stock" : "Currently unavailable"} · {product.city}</p>
      </div>
    </Link>
  );
}
