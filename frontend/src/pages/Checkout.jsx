import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { ArrowUpRight } from "lucide-react";
import { API, errMsg, imgFallback, inr, logWarn, priceText } from "@/lib/store";
import { useProduct } from "@/hooks/useProduct";
import { Header, Loading, NotFound } from "@/components/store/Header";
import { DiscountField } from "@/components/store/DiscountField";

const fetchPromoDeal = async productId => {
  const promo = await axios.get(`${API}/store/promo`);
  if (!promo.data) return null;
  const r = await axios.post(`${API}/discounts/validate`, { code: promo.data.code, product_id: productId });
  return r.data;
};

function CheckoutProgress({ free, hasDiscount }) {
  return (
    <div className="checkout-progress" data-testid="checkout-progress">
      <span className="progress-active"><b>01</b> Details</span><i></i>
      <span className={hasDiscount ? "progress-active" : ""}><b>02</b> {free ? "Free download" : "Payment"}</span><i></i>
      <span><b>03</b> {free ? "Ready" : "Access"}</span>
    </div>
  );
}

function Summary({ p, deal }) {
  return (
    <div className="summary">
      <img src={p.image_url || imgFallback} alt="" />
      <span><b>{p.name}</b><small>Digital download</small></span>
      <strong data-testid="checkout-price">{deal ? <><s className="was">{inr(p.price)}</s> {inr(deal.final)}</> : priceText(p)}</strong>
    </div>
  );
}

function CheckoutForm({ p }) {
  const nav = useNavigate();
  const free = p.price === 0;
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [deal, setDeal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (p.price > 0) fetchPromoDeal(p.id).then(d => d && setDeal(d)).catch(logWarn("Auto promo not applied"));
  }, [p.id, p.price]);
  const buy = async e => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await axios.post(`${API}/payments/checkout`, { product_id: p.id, customer_email: email, discount_code: deal?.code || code.trim() });
      nav(r.data.free ? `/payment/success?session_id=${r.data.session_id}` : `/pay/${r.data.session_id}`);
    } catch (err) {
      setError(errMsg(err));
      setDeal(null);
      setBusy(false);
    }
  };
  return (
    <>
      <CheckoutProgress free={free} hasDiscount={free || !!deal} />
      <Link to={`/product/${p.id}`} className="back-link" data-testid="checkout-back-link">← Back to product</Link>
      <div className="checkout-panel">
        <div>
          <p className="eyebrow">YOUR DOWNLOAD</p>
          <h1>One good thing,<br /><i>on its way.</i></h1>
          <p>Enter your email, then {free ? "we'll send your template instantly." : "pay with GPay. Your download unlocks as soon as the payment is confirmed."} No account needed.</p>
        </div>
        <form onSubmit={buy} data-testid="checkout-form">
          <Summary p={p} deal={deal} />
          <label>Email address<input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" data-testid="checkout-email-input" /></label>
          {!free && <DiscountField productId={p.id} code={code} setCode={setCode} deal={deal} setDeal={setDeal} />}
          {error && <p className="form-error" data-testid="checkout-error">{error}</p>}
          <button className="dark-button full" disabled={busy} data-testid="checkout-submit-button">{busy ? "Preparing…" : free ? "Get my free template" : "Continue to GPay"}<ArrowUpRight size={16} /></button>
          <small className="checkout-fine">{free ? "Free forever · Instant email · No subscription" : "GPay / UPI · No account needed · No subscription"}</small>
        </form>
      </div>
    </>
  );
}

export default function Checkout() {
  const { id } = useParams();
  const { product, missing } = useProduct(id);
  if (missing) return <NotFound what="product" />;
  if (!product) return <Loading text="Preparing checkout…" />;
  return <><Header /><main className="checkout"><CheckoutForm p={product} /></main></>;
}
