import { FormEvent, useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { Search, ShoppingBag, UserRound } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

export function StoreLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  function onSearch(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <div className="min-h-screen">
      <div className="bg-navy py-2 text-center text-xs tracking-wide text-white/90">
        Complimentary shipping across India on orders over ₹999 · Thoughtful retail, delivered
      </div>
      <header className="sticky top-0 z-40 border-b border-navy/10 bg-cream/95 backdrop-blur">
        <div className="container-sn flex items-center gap-4 py-4">
          <Link to="/" className="font-extrabold tracking-[0.18em] text-navy">
            SHOPNOVA
          </Link>
          <nav className="hidden items-center gap-6 text-sm font-medium text-navy/80 md:flex">
            <Link to="/">Home</Link>
            <Link to="/shop">Shop</Link>
            <Link to="/categories">Categories</Link>
            <Link to="/deals">Deals</Link>
          </nav>
          <form onSubmit={onSearch} className="relative ml-auto hidden flex-1 max-w-md md:block">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-mist" />
            <input className="input pl-9" placeholder="Search products" value={q} onChange={(e) => setQ(e.target.value)} />
          </form>
          <Link to="/account" className="ml-auto md:ml-0" aria-label="Account">
            <UserRound className="h-5 w-5" />
          </Link>
          <Link to="/cart" aria-label="Cart">
            <ShoppingBag className="h-5 w-5" />
          </Link>
          {user?.role === "ADMIN" ? (
            <Link to="/admin" className="hidden text-xs font-semibold uppercase tracking-wide text-coral md:inline">
              Admin
            </Link>
          ) : null}
        </div>
      </header>
      <Outlet />
      <footer className="mt-16 border-t border-navy/10 bg-white">
        <div className="container-sn grid gap-8 py-12 md:grid-cols-4">
          <div>
            <p className="font-extrabold tracking-[0.18em] text-navy">SHOPNOVA</p>
            <p className="mt-3 text-sm text-mist">A quieter way to shop for Indian homes — from Bengaluru ateliers to Jaipur looms.</p>
          </div>
          <div>
            <p className="text-sm font-semibold">Visit</p>
            <div className="mt-3 space-y-2 text-sm text-mist">
              <Link to="/shop" className="block">Shop</Link>
              <Link to="/categories" className="block">Categories</Link>
              <Link to="/deals" className="block">Deals</Link>
            </div>
          </div>
          <div>
            <p className="text-sm font-semibold">Help</p>
            <div className="mt-3 space-y-2 text-sm text-mist">
              <p>Cash on delivery available</p>
              <p>Simulated card checkout for the MVP</p>
              <p>support@shopnova.test</p>
            </div>
          </div>
          <div>
            <p className="text-sm font-semibold">{user ? `Hello, ${user.full_name.split(" ")[0]}` : "Account"}</p>
            <div className="mt-3 space-y-2 text-sm text-mist">
              {user ? (
                <button onClick={logout} className="text-left">Sign out</button>
              ) : (
                <Link to="/login" className="block">Sign in</Link>
              )}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
