import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/services/api";
import { Button, Card } from "@/components/ui";
import type { User } from "@/types";

export function AccountPage() {
  const { user, logout } = useAuth();
  const { data: profile, isLoading } = useQuery<User>({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/api/auth/me"),
    enabled: Boolean(user),
  });

  if (isLoading) return <div className="container-sn py-16">Loading…</div>;
  if (!user) return <div className="container-sn py-16">Not signed in.</div>;

  const me = profile ?? user;

  return (
    <div className="container-sn py-10 lg:max-w-2xl">
      <Card className="p-10">
        <h2 className="text-2xl font-bold text-navy mb-6">Account</h2>
        <div className="space-y-4 text-sm">
          <div className="flex justify-between border-b pb-3">
            <span className="text-mist">Name</span>
            <span className="font-semibold">{me.full_name}</span>
          </div>
          <div className="flex justify-between border-b pb-3">
            <span className="text-mist">Email</span>
            <span className="font-semibold">{me.email}</span>
          </div>
          <div className="flex justify-between border-b pb-3">
            <span className="text-mist">Phone</span>
            <span className="font-semibold">{me.phone || "—"}</span>
          </div>
          <div className="flex justify-between border-b pb-3">
            <span className="text-mist">Role</span>
            <span className="font-semibold">{me.role}</span>
          </div>
        </div>
        <p className="mt-6 text-sm text-mist">
          Orders and addresses can be managed from My Orders and Checkout.
        </p>
        <Button className="mt-4" onClick={logout}>
          Sign out
        </Button>
      </Card>
    </div>
  );
}
