import { useEffect } from "react";
import {
  Routes,
  Route,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { StoreLayout } from "@/layouts/StoreLayout";
import { AdminLayout } from "@/layouts/AdminLayout";
import { HomePage } from "@/pages/Home";
import { ShopPage } from "@/pages/Shop";
import { SearchPage } from "@/pages/Search";
import { ProductPage } from "@/pages/Product";
import { CartPage } from "@/pages/Cart";
import { CheckoutPage } from "@/pages/Checkout";
import { OrderConfirmationPage } from "@/pages/OrderConfirmation";
import { MyOrdersPage } from "@/pages/MyOrders";
import { OrderDetailPage } from "@/pages/OrderDetail";
import { LoginPage } from "@/pages/Login";
import { RegisterPage } from "@/pages/Register";
import { AccountPage } from "@/pages/Account";
import { AdminDashboardPage } from "@/pages/admin/Dashboard";
import { AdminProductsPage } from "@/pages/admin/Products";
import { AdminCategoriesPage } from "@/pages/admin/Categories";
import { AdminOrdersPage } from "@/pages/admin/Orders";
import { AdminInventoryPage } from "@/pages/admin/Inventory";
import { AdminCustomersPage } from "@/pages/admin/Customers";
import { AdminEventsPage } from "@/pages/admin/Events";
import { AdminSearchPage } from "@/pages/admin/Search";
import { AdminHealthPage } from "@/pages/admin/Health";

const AdminRoutes = () => (
  <Routes>
    <Route path="/" element={<AdminDashboardPage />} />
    <Route path="products" element={<AdminProductsPage />} />
    <Route path="categories" element={<AdminCategoriesPage />} />
    <Route path="orders" element={<AdminOrdersPage />} />
    <Route path="inventory" element={<AdminInventoryPage />} />
    <Route path="customers" element={<AdminCustomersPage />} />
    <Route path="events" element={<AdminEventsPage />} />
    <Route path="search" element={<AdminSearchPage />} />
    <Route path="health" element={<AdminHealthPage />} />
  </Routes>
);

export default function App() {
  const { user, loading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user && location.pathname === "/login") {
      navigate(user.role === "ADMIN" ? "/admin" : "/", { replace: true });
    }
  }, [loading, user, location.pathname, navigate]);

  if (loading) return null;

  return (
    <Routes>
      <Route path="/" element={<StoreLayout />}>
        <Route index element={<HomePage />} />
        <Route path="shop" element={<ShopPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="product/:id" element={<ProductPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="order-confirmation/:id" element={<OrderConfirmationPage />} />
        <Route path="orders" element={<MyOrdersPage />} />
        <Route path="orders/:id" element={<OrderDetailPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="account" element={<AccountPage />} />
        <Route
          path="admin"
          element={
            user?.role === "ADMIN" ? (
              <AdminLayout>
                <AdminRoutes />
              </AdminLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
