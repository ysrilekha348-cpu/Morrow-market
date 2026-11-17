import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Clock, Download, X } from "lucide-react";
import { API, logWarn } from "@/lib/store";
import { Header, Loading, NotFound } from "@/components/store/Header";

function useOrderStatus(sid) {
  const [order, setOrder] = useState(null);
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    const get = () => axios.get(`${API}/payments/status/${sid}`).then(r => setOrder(r.data)).catch(e => {
      if (e?.response?.status === 404) setMissing(true);
      else logWarn("Order status check failed")(e);
    });
    get();
    const t = setInterval(get, 15000);
    return () => clearInterval(t);
  }, [sid]);
  return { order, missing };
}

const statusLabel = (free, state) => (free ? "TEMPLATE READY" : { paid: "PAYMENT CONFIRMED", rejected: "PAYMENT NOT CONFIRMED" }[state] || "PAYMENT BEING CHECKED");
const HEADLINES = {
  paid: <>Your next chapter<br /><i>starts here.</i></>,
  rejected: <>Let's sort<br /><i>this out.</i></>,
  pending: <>Almost<br /><i>there.</i></>,
};
const ICONS = { paid: "✓", rejected: <X size={22} />, pending: <Clock size={22} /> };

function StatusBody({ order, state, free }) {
  if (state === "paid") return (
    <>
      <p>{free ? "Your free template is ready whenever you are." : "Your download is ready whenever you are."}</p>
      <a href={`${API}/downloads/${order.session_id}`} className="dark-button" data-testid="download-product-button"><Download size={16} /> Download {order.product_name}</a>
    </>
  );
  if (state === "rejected") return (
    <>
      <p>We couldn't match your payment reference. Please check it and resend.</p>
      <Link to={`/pay/${order.session_id}`} className="dark-button" data-testid="retry-payment-button">Resend transaction ID</Link>
    </>
  );
  return <p data-testid="order-pending-note">We've received your transaction ID for {order.product_name}. Keep this page open or bookmark it. Your download appears here once the payment is confirmed.</p>;
}

export default function Success() {
  const [params] = useSearchParams();
  const { order, missing } = useOrderStatus(params.get("session_id"));
  if (missing) return <NotFound what="order" />;
  if (!order) return <Loading text="Checking your order…" />;
  const free = order.amount === 0;
  const state = ["paid", "rejected"].includes(order.payment_status) ? order.payment_status : "pending";
  return (
    <>
      <Header />
      <main className="success" data-testid="order-status-page">
        <div className={`success-icon ${state === "paid" ? "" : "pending"}`}>{ICONS[state]}</div>
        <p className="eyebrow" data-testid="order-status-label">{statusLabel(free, state)}</p>
        <h1>{HEADLINES[state]}</h1>
        <StatusBody order={order} state={state} free={free} />
        <Link to="/" className="back-link" data-testid="success-home-link">Return to Morrow market</Link>
      </main>
    </>
  );
}
