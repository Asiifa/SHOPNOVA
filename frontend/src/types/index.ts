export type User = {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  role: "CUSTOMER" | "ADMIN";
};

export type Category = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  image_url?: string | null;
};

export type Product = {
  id: string;
  name: string;
  slug: string;
  description: string;
  sku: string;
  brand: string;
  price: number;
  discount_price?: number | null;
  city: string;
  image_url: string;
  specifications: Record<string, string>;
  rating: number;
  review_count: number;
  sold_count: number;
  available_quantity: number;
  category_name?: string | null;
  category_slug?: string | null;
  images: string[];
};

export type Cart = {
  id: string;
  items: {
    id: string;
    product_id: string;
    name: string;
    brand: string;
    image_url: string;
    unit_price: number;
    quantity: number;
    available_quantity: number;
    line_total: number;
  }[];
  subtotal: number;
  shipping: number;
  total: number;
};

export type Address = {
  id: string;
  label: string;
  full_name: string;
  phone: string;
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  pin_code: string;
  is_default: boolean;
};

export type Order = {
  id: string;
  order_number: string;
  total_amount: number;
  shipping_amount: number;
  payment_method: string;
  payment_status: string;
  order_status: string;
  created_at: string;
  items: {
    product_id: string;
    product_name: string;
    sku: string;
    unit_price: number;
    quantity: number;
    line_total: number;
  }[];
};
