import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/services/api";
import { useToast } from "@/contexts/ToastContext";
import { Button, Input, Card } from "@/components/ui";
import { z } from "zod";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  full_name: z.string().min(2, "Full name is required"),
  phone: z.string().min(10, "Enter a valid phone number").optional().or(z.literal("")),
});

export function RegisterPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", phone: "" });
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
      await api.post("/api/auth/register", {
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        phone: form.phone || undefined,
      });
      toast("Account created. You are signed in.");
      navigate("/");
    } catch (e: any) {
      toast(e.message || "Registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container-sn py-12 lg:max-w-md">
      <Card className="p-10">
        <h2 className="text-2xl font-bold text-navy mb-2">Create an account</h2>
        <p className="text-mist text-sm mb-8">Join SHOPNOVA and start shopping.</p>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Full name</label>
            <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            {errors.full_name && <p className="text-xs text-danger">{errors.full_name}</p>}
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Email</label>
            <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            {errors.email && <p className="text-xs text-danger">{errors.email}</p>}
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Phone</label>
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            {errors.phone && <p className="text-xs text-danger">{errors.phone}</p>}
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Password</label>
            <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            {errors.password && <p className="text-xs text-danger">{errors.password}</p>}
          </div>
          <Button className="w-full" disabled={submitting} type="submit">
            Create account
          </Button>
        </form>
        <p className="mt-6 text-sm text-center text-mist">
          Already have an account?{" "}
          <a href="/login" className="text-coral hover:underline font-medium">
            Sign in
          </a>
        </p>
      </Card>
    </div>
  );
}
