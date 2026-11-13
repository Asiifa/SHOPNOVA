import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Button, Input, Card } from "@/components/ui";
import { z } from "zod";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export function LoginPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    const parsed = schema.safeParse(form);
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      parsed.error.errors.forEach((err) => {
        fieldErrors[err.path[0] as string] = err.message;
      });
      setErrors(fieldErrors);
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/auth/login", { email: form.email, password: form.password });
      navigate("/");
    } catch (e: any) {
      toast(e.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container-sn py-12 lg:max-w-md">
      <Card className="p-10">
        <h2 className="text-2xl font-bold text-navy mb-2">Welcome back</h2>
        <p className="text-mist text-sm mb-8">Sign in to your SHOPNOVA account</p>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Email</label>
            <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            {errors.email && <p className="text-xs text-danger">{errors.email}</p>}
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Password</label>
            <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            {errors.password && <p className="text-xs text-danger">{errors.password}</p>}
            {errors._form && <p className="text-xs text-danger">{errors._form}</p>}
          </div>
          <Button className="w-full" disabled={submitting} type="submit">
            Sign in
          </Button>
        </form>
        <p className="mt-6 text-sm text-center text-mist">
          New to SHOPNOVA?{" "}
          <a href="/register" className="text-coral hover:underline font-medium">
            Create an account
          </a>
        </p>
      </Card>
    </div>
  );
}
