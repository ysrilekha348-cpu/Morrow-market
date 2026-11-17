import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { SignInButton, useAuth } from "@clerk/react";
import axios from "axios";
import { Lock, Plus, TrendingUp } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { API, inr, logWarn } from "@/lib/store";
import { Header } from "@/components/store/Header";
import { OrdersSection } from "@/components/admin/Orders";
import { PaymentSettings } from "@/components/admin/PaymentSettings";
import { Discounts } from "@/components/admin/Discounts";
import { Reports } from "@/components/admin/Reports";
import { AddProductForm, ProductsSection } from "@/components/admin/Products";

function useAdminData(isSignedIn, getToken) {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [denied, setDenied] = useState(false);
  const auth = useCallback(async () => ({ headers: { Authorization: `Bearer ${await getToken()}` } }), [getToken]);
  const load = useCallback(async () => {
    const config = await auth();
    axios.get(`${API}/admin/products`, config).then(r => setProducts(r.data)).catch(e => {
      if ([401, 403].includes(e?.response?.status)) setDenied(true);
      else logWarn("Products failed to load")(e);
    });
    axios.get(`${API}/admin/orders`, config).then(r => setOrders(r.data)).catch(logWarn("Orders failed to load"));
  }, [auth]);
  useEffect(() => { if (isSignedIn) load(); }, [isSignedIn, load]);
  return { products, orders, denied, auth, load };
}

function SalesOverview({ orders }) {
  const data = useMemo(() => {
    const keyFormat = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" });
    const labelFormat = new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short" });
    const days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      const key = keyFormat.format(date);
      return { key, day: labelFormat.format(date), revenue: 0, orders: 0 };
    });
    const byDay = new Map(days.map(d => [d.key, d]));
    orders.filter(o => o.payment_status === "paid" && o.created_at).forEach(o => {
      const date = new Date(o.created_at);
      if (Number.isNaN(date.getTime())) return;
      const day = byDay.get(keyFormat.format(date));
      if (day) { day.revenue += Number(o.amount) || 0; day.orders += 1; }
    });
    return days;
  }, [orders]);
  const total = data.reduce((sum, d) => sum + d.revenue, 0);
  return (
    <section className="admin-section sales-overview" data-testid="sales-overview">
      <div className="section-label"><TrendingUp size={18} /><h2>Last 7 days</h2></div>
      {total > 0 ? (
        <>
          <div className="sales-chart" role="img" aria-label="Confirmed sales revenue by day for the last seven days">
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d9dbd2" />
                <XAxis dataKey="day" tick={{ fill: "#788077", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#788077", fontSize: 10 }} axisLine={false} tickLine={false} width={48} />
                <Tooltip formatter={value => [`₹${Number(value).toLocaleString("en-IN")}`, "Confirmed revenue"]} />
                <Bar dataKey="revenue" fill="#b58e3d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="sales-caption">{data.reduce((sum, d) => sum + d.orders, 0)} confirmed orders · ₹{total.toLocaleString("en-IN")} revenue in the last seven days</p>
        </>
      ) : <p className="empty">Confirmed sales will appear here once your first payment is approved.</p>}
    </section>
  );
}

function SignInWall() {
  return (
    <div className="auth-wall">
      <Lock size={24} /><h1>Owner space</h1><p>Sign in to manage your collection.</p>
      <SignInButton mode="redirect"><button className="dark-button" data-testid="admin-sign-in-button">Sign in</button></SignInButton>
    </div>
  );
}

function DeniedWall() {
  return (
    <div className="auth-wall" data-testid="admin-denied">
      <Lock size={24} /><h1>Owners only</h1><p>This account doesn't have access to the owner space.</p>
      <Link to="/" className="dark-button">Back to the store</Link>
    </div>
  );
}

function Stats({ products, orders }) {
  const revenue = orders.filter(o => o.payment_status === "paid").reduce((s, o) => s + o.amount, 0);
  const pending = orders.filter(o => o.payment_status === "pending_review").length;
  return (
    <div className="stats">
      <div><span>Published products</span><b data-testid="stat-products">{products.filter(p => p.published).length}</b></div>
      <div><span>Payments to review</span><b data-testid="stat-pending">{pending}</b></div>
      <div><span>Revenue (confirmed)</span><b data-testid="stat-revenue">{inr(revenue)}</b></div>
    </div>
  );
}

export default function Admin() {
  const { isSignedIn, getToken } = useAuth();
  const { products, orders, denied, auth, load } = useAdminData(isSignedIn, getToken);
  const [showForm, setShowForm] = useState(false);
  if (!isSignedIn) return <SignInWall />;
  if (denied) return <DeniedWall />;
  const onSaved = () => { setShowForm(false); load(); };
  return (
    <>
      <Header />
      <main className="admin">
        <div className="admin-head">
          <div><p className="eyebrow">PRIVATE WORKSPACE</p><h1>Good morning,<br /><i>maker.</i></h1></div>
          <button className="dark-button" onClick={() => setShowForm(!showForm)} data-testid="add-product-button"><Plus size={16} /> {showForm ? "Close" : "Add product"}</button>
        </div>
        {showForm && <AddProductForm auth={auth} onSaved={onSaved} />}
        <Stats products={products} orders={orders} />
        <SalesOverview orders={orders} />
        <OrdersSection orders={orders} auth={auth} onDone={load} />
        <Reports auth={auth} />
        <PaymentSettings auth={auth} />
        <Discounts auth={auth} />
        <ProductsSection products={products} auth={auth} onDone={load} />
      </main>
    </>
  );
}
