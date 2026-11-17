import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SignInButton, useAuth } from "@clerk/react";
import axios from "axios";
import { Lock, Plus } from "lucide-react";
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
        <OrdersSection orders={orders} auth={auth} onDone={load} />
        <Reports auth={auth} />
        <PaymentSettings auth={auth} />
        <Discounts auth={auth} />
        <ProductsSection products={products} auth={auth} onDone={load} />
      </main>
    </>
  );
}
