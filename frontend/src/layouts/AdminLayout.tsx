import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import type { ReactNode } from "react";

const links = [
  ["Overview", "/admin"],
  ["Products", "/admin/products"],
  ["Categories", "/admin/categories"],
  ["Orders", "/admin/orders"],
  ["Inventory", "/admin/inventory"],
  ["Customers", "/admin/customers"],
  ["Kafka events", "/admin/events"],
  ["Search sync", "/admin/search"],
  ["Health", "/admin/health"],
];

export function AdminLayout({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "ADMIN") return <Navigate to="/" replace />;
  return (
    <div className="min-h-screen bg-[#eef1f4] md:grid md:grid-cols-[240px_1fr]">
      <aside className="bg-navy p-6 text-white">
        <Link to="/" className="text-xs font-bold tracking-[0.2em]">SHOPNOVA</Link>
        <p className="mt-2 text-sm text-white/70">Administration</p>
        <nav className="mt-8 space-y-2 text-sm">
          {links.map(([label, href]) => (
            <Link key={href} to={href} className="block rounded-lg px-3 py-2 text-white/85 hover:bg-white/10">
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="p-6 md:p-10">{children}</main>
    </div>
  );
}
