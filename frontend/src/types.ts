export type UserRole = "CUSTOMER" | "ADMIN";

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  image_url: string | null;
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  short_description: string | null;
  base_price: number;
  discount_price: number | null;
  price: number;
  sku: string;
  stock_quantity: number;
  available_quantity: number;
  category_id: string | null;
  category_slug: string | null;
  category?: Category;
  brand: string | null;
  city: string | null;
  image_url: string | null;
  images: string[];
  specifications: Record<string, string | number | boolean> | null;
  is_active: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: UserRole;
}

export interface CartItem {
  id: string;
  product_id: string;
  name: string;
  brand: string;
  image_url: string;
  unit_price: number;
  quantity: number;
  available_quantity: number;
  line_total: number;
}

export interface Cart {
  id: string;
  items: CartItem[];
  subtotal: number;
  shipping: number;
  total: number;
}

export interface OrderItem {
  id: string;
  product_name: string;
  sku: string;
  quantity: number;
  line_total: number;
}

export interface OrderCustomer {
  full_name: string;
  email: string;
}

export interface Order {
  id: string;
  order_number: string;
  order_status: string;
  created_at: string;
  total_amount: number;
  items: OrderItem[];
  customer?: OrderCustomer;
  payment_method: string;
}

export interface PaginatedOrders {
  items: Order[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}
