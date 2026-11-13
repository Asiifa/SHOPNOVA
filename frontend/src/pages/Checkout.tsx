import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api, inr } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { Button, Input, Card, SkeletonCircle } from "@/components/ui";
import { z } from "zod";
import type { Cart } from "@/types";

const CheckoutSchema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  email: z.string().email("Enter a valid email"),
  phone: z.string().min(10, "Enter a valid phone number"),
  label: z.string().min(1, "Address label is required"),
  line1: z.string().min(4, "Street address is required"),
  line2: z.string().optional(),
  city: z.string().min(2, "City is required"),
  state: z.string().min(2, "State is required"),
  pin_code: z.string().min(6, "Enter a valid PIN code"),
});

export function CheckoutPage() {
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  if (!user) {
    navigate("/login");
    return null;
  }

  const [cart, setCart] = useState<Cart | null>(null);
  const [loadingCart, setLoadingCart] = useState(true);
  const [form, setForm] = useState<z.infer<typeof CheckoutSchema>>({
    full_name: user.full_name || "",
    email: user.email || "",
    phone: user.phone || "",
    label: "Home",
    line1: "",
    line2: "",
    city: "",
    state: "",
    pin_code: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  async function loadCart() {
    setLoadingCart(true);
    try {
      setCart(await api.get<Cart>("/api/cart"));
    } catch (e: any) {
      toast(e.message || "Unable to load cart");
    } finally {
      setLoadingCart(false);
    }
  }

  useEffect(() => {
    loadCart();
  }, []);

  if (loadingCart) return <div className="container-sn py-16"><SkeletonCircle className="mx-auto" /></div>;
  if (!cart || cart.items.length === 0) {
    navigate("/cart");
    return null;
  }

  function handleChange(k: string, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
    if (errors[k]) setErrors((p) => { const n = { ...p }; delete n[k]; return n; });
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = CheckoutSchema.safeParse(form);
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
      const address = await api.post<{ id: string }>("/api/addresses", {
        label: form.label,
        full_name: form.full_name,
        phone: form.phone,
        line1: form.line1,
        line2: form.line2 || undefined,
        city: form.city,
        state: form.state,
        pin_code: form.pin_code,
      });
      const order = await api.post<{ id: string }>("/api/orders", {
        address_id: address.id,
        payment_method: "COD",
      });
      navigate(`/order-confirmation/${order.id}`);
    } catch (e: any) {
      toast(e.message || "Unable to place order");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container-sn py-10 lg:grid lg:grid-cols-3 lg:gap-10">
      <div className="lg:col-span-2">
        <h2 className="text-2xl font-bold text-navy mb-8">Checkout — Cash on Delivery</h2>
        <p className="text-mist text-sm mb-8">
          Demo payment flow for this hackathon MVP. No real card details are collected or processed.
        </p>
        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">Full name</label>
              <Input value={form.full_name} onChange={(e) => handleChange("full_name", e.target.value)} />
              {errors.full_name && <p className="text-xs text-danger">{errors.full_name}</p>}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">Email</label>
              <Input type="email" value={form.email} onChange={(e) => handleChange("email", e.target.value)} />
              {errors.email && <p className="text-xs text-danger">{errors.email}</p>}
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Phone</label>
            <Input value={form.phone} onChange={(e) => handleChange("phone", e.target.value)} />
            {errors.phone && <p className="text-xs text-danger">{errors.phone}</p>}
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">Address label</label>
              <Input value={form.label} onChange={(e) => handleChange("label", e.target.value)} />
              {errors.label && <p className="text-xs text-danger">{errors.label}</p>}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">Street address</label>
              <Input value={form.line1} onChange={(e) => handleChange("line1", e.target.value)} />
              {errors.line1 && <p className="text-xs text-danger">{errors.line1}</p>}
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-navy">Address line 2 (optional)</label>
            <Input value={form.line2} onChange={(e) => handleChange("line2", e.target.value)} />
          </div>
          <div className="grid gap-5 sm:grid-cols-3">
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">City</label>
              <Input value={form.city} onChange={(e) => handleChange("city", e.target.value)} />
              {errors.city && <p className="text-xs text-danger">{errors.city}</p>}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">State</label>
              <Input value={form.state} onChange={(e) => handleChange("state", e.target.value)} />
              {errors.state && <p className="text-xs text-danger">{errors.state}</p>}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-navy">PIN code</label>
              <Input value={form.pin_code} onChange={(e) => handleChange("pin_code", e.target.value)} />
              {errors.pin_code && <p className="text-xs text-danger">{errors.pin_code}</p>}
            </div>
          </div>
          <Button className="w-full" disabled={submitting} type="submit">
            Place order — ₹{Math.round(cart.total)}
          </Button>
        </form>
      </div>
      <div className="lg:col-span-1 mt-10 lg:mt-0">
        <Card className="p-8">
          <h3 className="font-semibold text-navy mb-6">Order summary</h3>
          <div className="space-y-4">
            {cart.items.map((item: any) => (
              <div key={item.id} className="flex gap-3 text-sm">
                <img src={item.image_url} alt={item.name} className="w-12 h-12 rounded-xl object-cover flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-medium">{item.name} × {item.quantity}</div>
                  <div className="text-mist text-xs">{item.brand}</div>
                </div>
                <div className="font-semibold">{inr(item.line_total)}</div>
              </div>
            ))}
            <div className="mt-4 pt-4 border-t border-navy/10 space-y-2 text-sm">
              <div className="flex justify-between">Subtotal <span>{inr(cart.subtotal)}</span></div>
              {cart.shipping > 0 ? (
                <div className="flex justify-between">Shipping <span>{inr(cart.shipping)}</span></div>
              ) : (
                <div className="flex justify-between text-success">Shipping <span>Free</span></div>
              )}
              <div className="flex justify-between text-navy font-bold">
                Total <span>{inr(cart.total)}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
