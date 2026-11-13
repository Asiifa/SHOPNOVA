import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { CheckoutPage } from "@/pages/Checkout";
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
  email: "",
  full_name: "",
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

const cart: Cart = {
  id: "c-1",
  items: [
    {
      id: "ci-1",
      product_id: "p-1",
      name: "Bluetooth Earphones",
      brand: "TestBrand",
      image_url: "https://example.com/img.jpg",
      unit_price: 1499,
      quantity: 1,
      available_quantity: 10,
      line_total: 1499,
    },
  ],
  subtotal: 1499,
  shipping: 49,
  total: 1548,
};

beforeEach(() => {
  vi.mocked(api.get).mockReset();
  vi.mocked(api.post).mockReset();
  vi.mocked(api.put).mockReset();
  vi.mocked(api.delete).mockReset();
  vi.mocked(api.patch).mockReset();
});

describe("CheckoutPage", () => {
  it("shows validation errors on empty submit", async () => {
    vi.mocked(api.get).mockResolvedValueOnce(cart);
    renderWithProviders(<CheckoutPage />);
    await waitFor(() => screen.getByText(/order summary/i));
    fireEvent.click(screen.getByRole("button", { name: /place order/i }));
    await waitFor(() => screen.getByText(/full name is required/i));
    expect(vi.mocked(api.post)).not.toHaveBeenCalledWith(
      "/api/orders",
      expect.objectContaining({ payment_method: "COD" })
    );
  });

  it("places a COD order and navigates to confirmation", async () => {
    vi.mocked(api.get).mockResolvedValueOnce(cart);
    vi.mocked(api.post).mockResolvedValueOnce({ id: "a-1" });
    vi.mocked(api.post).mockResolvedValueOnce({ id: "o-1" });
    renderWithProviders(<CheckoutPage />);
    await waitFor(() => screen.getByText(/order summary/i));

    const boxes = screen.getAllByRole("textbox");
    fireEvent.change(boxes[0], { target: { value: "Priya Sharma" } }); // full_name
    fireEvent.change(boxes[1], { target: { value: "priya@example.com" } }); // email
    fireEvent.change(boxes[2], { target: { value: "9876500001" } }); // phone
    fireEvent.change(boxes[3], { target: { value: "Home" } }); // label
    fireEvent.change(boxes[4], { target: { value: "1, Test Street" } }); // line1
    fireEvent.change(boxes[5], { target: { value: "Apt 4" } }); // line2
    fireEvent.change(boxes[6], { target: { value: "Bengaluru" } }); // city
    fireEvent.change(boxes[7], { target: { value: "Karnataka" } }); // state
    fireEvent.change(boxes[8], { target: { value: "560095" } }); // pin_code

    fireEvent.click(screen.getByRole("button", { name: /place order/i }));
    await waitFor(() => expect(vi.mocked(api.post)).toHaveBeenCalledWith("/api/orders", expect.anything()));
    expect(vi.mocked(api.post)).toHaveBeenCalledWith("/api/orders", {
      address_id: "a-1",
      payment_method: "COD",
    });
  });
});
