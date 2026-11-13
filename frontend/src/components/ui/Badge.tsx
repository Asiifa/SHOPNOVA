export function Badge({ children, variant = "neutral" }: { children: React.ReactNode; variant?: "neutral" | "ok" | "warn" | "danger" }) {
  const base = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold";
  const variants: Record<string, string> = {
    neutral: "bg-navy/5 text-navy",
    ok: "bg-success/10 text-success",
    warn: "bg-[#F4C28A]/20 text-[#8A5A1A]",
    danger: "bg-danger/10 text-danger",
  };
  return <span className={`${base} ${variants[variant]}`}>{children}</span>;
}
