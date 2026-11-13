import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api, inr } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { Button, Input, Card, SkeletonCircle, EmptyState } from "@/components/ui";
import type { Cart, CartItem } from "@/types";

export function CartPage() {
  const { user } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  if (!user) {
    navigate("/login");
    return null;
  }

  const { data: cart, isLoading } = useQuery<Cart>({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/api/cart"),
  });

  const updateItem = useMutation({
    mutationFn: ({ id, quantity }: { id: string; quantity: number }) =>
      api.put(`/api/cart/items/${id}`, { quantity }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      toast("Cart updated");
    },
    onError: (err: any) => toast(err.message || "Unable to update quantity"),
  });

  const removeItem = useMutation({
    mutationFn: (id: string) => api.delete(`/api/cart/items/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      toast("Removed from cart");
    },
    onError: (err: any) => toast(err.message || "Unable to remove item"),
  });

  if (isLoading) return <div className="container-sn py-16"><SkeletonCircle className="mx-auto" /></div>;
  if (!cart || cart.items.length === 0) {
    return (
      <div className="container-sn py-16">
        <EmptyState
          title="Your cart is empty"
          description="Add products from the shop to get started."
          action={<Link to="/shop" className="btn-primary">Browse products</Link>}
        />
      </div>
    );
  }

  return (
    <div className="container-sn py-10 lg:grid lg:grid-cols-3 lg:gap-10">
      <div className="lg:col-span-2">
        <h2 className="text-2xl font-bold text-navy mb-8">Shopping cart</h2>
        <div className="space-y-5">
          {cart.items.map((item: CartItem) => (
            <Card key={item.id} className="p-5 flex gap-4 items-start">
              <img src={item.image_url} alt={item.name} className="w-28 h-36 rounded-2xl object-cover flex-shrink-0" />
              <div className="flex flex-col flex-1">
                <h3 className="font-semibold text-navy line-clamp-2">{item.name}</h3>
                <p className="mt-1 text-xs text-mist">{item.brand}</p>
                <p className="mt-2 font-medium">{inr(item.unit_price)}</p>
                <div className="mt-3 flex items-center gap-3">
                  <Input
                    type="number"
                    min="1"
                    max={item.available_quantity}
                    value={item.quantity}
                    className="w-20"
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      if (v >= 1) updateItem.mutate({ id: item.id, quantity: v });
                    }}
                  />
                  <button
                    onClick={() => removeItem.mutate(item.id)}
                    className="text-xs text-danger hover:underline"
                  >
                    Remove
                  </button>
                </div>
                {item.quantity > item.available_quantity && (
                  <p className="mt-2 text-xs text-danger">Only {item.available_quantity} left in stock.</p>
                )}
              </div>
              <div className="font-semibold">{inr(item.line_total)}</div>
            </Card>
          ))}
        </div>
      </div>
      <div className="lg:col-span-1 mt-10 lg:mt-0">
        <Card className="p-8">
          <h3 className="font-semibold text-navy mb-6">Order summary</h3>
          <div className="space-y-3 text-sm mb-8">
            <div className="flex justify-between">{cart.items.length} items <span>{inr(cart.subtotal)}</span></div>
            {cart.shipping > 0 ? (
              <div className="flex justify-between">Shipping <span>{inr(cart.shipping)}</span></div>
            ) : (
              <div className="flex justify-between text-success">Shipping <span>Free</span></div>
            )}
            <div className="flex justify-between text-navy font-bold pt-3 border-t border-navy/10">
              Total <span>{inr(cart.total)}</span>
            </div>
          </div>
          <Button
            className="w-full"
            onClick={() => navigate("/checkout")}
            disabled={cart.items.some((i) => i.quantity > i.available_quantity)}
          >
            Proceed to checkout
          </Button>
          {cart.items.some((i) => i.quantity > i.available_quantity) && (
            <p className="mt-3 text-xs text-danger">Some quantities exceed available stock. Please adjust.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
