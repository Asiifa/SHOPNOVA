import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { CartPage } from "@/pages/Cart";
import { api } from "@/services/api";
import type { Cart, User } from "@/types";
import type { ReactNode } from "react";

vi.mock("@/services/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  },
  inr: (v: number) => `₹${v}`,
}));

const user: User = {
  id: "u-1",
  email: "buyer@example.com",
  full_name: "Buyer",
  phone: null,
  role: "CUSTOMER",
};

vi.mock("@/contexts/AuthContext", async (orig) => {
  const actual = await orig<typeof import("@/contexts/AuthContext")>();
  return {
    ...actual,
    useAuth: vi.fn(() => ({ user, loading: false, login: vi.fn(), register: vi.fn(), logout: vi.fn() })),
  };
});

function renderWithProviders(ui: ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

const baseCart: Cart = {
  id: "c-1",
  items: [
    {
      id: "ci-1",
      product_id: "p-1",
      name: "NovaPulse Bluetooth Headphones",
      brand: "NovaPulse",
      image_url: "https://example.com/img.jpg",
      unit_price: 2499,
      quantity: 1,
      available_quantity: 48,
      line_total: 2499,
    },
  ],
  subtotal: 2499,
  shipping: 49,
  total: 2548,
};

beforeEach(() => {
  vi.mocked(api.get).mockReset();
  vi.mocked(api.put).mockReset();
  vi.mocked(api.delete).mockReset();
  vi.mocked(api.post).mockReset();
  vi.mocked(api.patch).mockReset();
});

describe("CartPage", () => {
  it("shows empty state when the cart is empty", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ id: "c-1", items: [], subtotal: 0, shipping: 0, total: 0 });
    renderWithProviders(<CartPage />);
    await waitFor(() => screen.getByText(/your cart is empty/i));
  });

  it("lists cart items and updates quantity", async () => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.put).mockReset();
    vi.mocked(api.get).mockResolvedValueOnce(baseCart);
    vi.mocked(api.put).mockResolvedValue({ ...baseCart });
    renderWithProviders(<CartPage />);
    await waitFor(() => screen.getByText("NovaPulse Bluetooth Headphones"));
    const input = screen.getByRole("spinbutton");
    fireEvent.change(input, { target: { value: "2" } });
    await waitFor(() => expect(vi.mocked(api.put)).toHaveBeenCalled());
    expect(vi.mocked(api.put)).toHaveBeenCalledWith("/api/cart/items/ci-1", { quantity: 2 });
  });

  it("removes an item", async () => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.delete).mockReset();
    vi.mocked(api.get).mockResolvedValueOnce(baseCart);
    vi.mocked(api.delete).mockResolvedValue({});
    renderWithProviders(<CartPage />);
    await waitFor(() => screen.getByText("NovaPulse Bluetooth Headphones"));
    fireEvent.click(screen.getByText("Remove"));
    await waitFor(() => expect(vi.mocked(api.delete)).toHaveBeenCalledWith("/api/cart/items/ci-1"));
  });
});
