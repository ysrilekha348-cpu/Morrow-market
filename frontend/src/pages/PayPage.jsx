import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { ArrowUpRight, QrCode } from "lucide-react";
import { API, errMsg, inr, logWarn } from "@/lib/store";
import { Header, Loading, NotFound } from "@/components/store/Header";

function usePayOrder(sessionId, nav) {
  const [order, setOrder] = useState(null);
  const [info, setInfo] = useState(null);
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    axios.get(`${API}/payments/status/${sessionId}`).then(r => {
      if (["pending_review", "paid"].includes(r.data.payment_status)) nav(`/payment/success?session_id=${sessionId}`, { replace: true });
      else setOrder(r.data);
    }).catch(() => setMissing(true));
    axios.get(`${API}/store/payment-info`).then(r => setInfo(r.data)).catch(logWarn("Payment info failed to load"));
  }, [sessionId, nav]);
  return { order, info, missing };
}

function PayInstructions({ order }) {
  return (
    <div>
      <p className="eyebrow">STEP 2 OF 2 · PAY WITH GPAY</p>
      <h1>Scan, pay,<br /><i>done.</i></h1>
      <ol className="pay-steps">
        <li>Open GPay or any UPI app.</li>
        <li>Scan the QR code or pay the number below.</li>
        <li>Pay exactly <b data-testid="pay-amount">{inr(order.amount)}</b>.</li>
        <li>Paste the transaction ID (UTR) here.</li>
      </ol>
      {order.payment_status === "rejected" && <p className="form-error" data-testid="pay-rejected-note">We couldn't confirm your last payment reference. Please check it and try again.</p>}
    </div>
  );
}

function PayDetails({ order, info }) {
  return (
    <>
      <div className={`qr-box ${info.has_qr ? "" : "empty"}`} data-testid="pay-qr-box">
        {info.has_qr
          ? <img src={`${API}/store/qr?v=${info.qr_version}`} alt="GPay QR code" data-testid="pay-qr-image" />
          : <div className="qr-empty"><QrCode size={34} /><span>QR coming soon. Pay the number below.</span></div>}
      </div>
      <div className="gpay-number"><span>GPay number</span><b data-testid="pay-gpay-number">{info.gpay_number}</b></div>
      <div className="summary compact">
        <span><b>{order.product_name}</b><small>{order.customer_email}{order.discount_code && <> · {order.discount_code} ({order.discount_percent}% off)</>}</small></span>
        <strong data-testid="pay-summary-price">{order.discount_code && <s className="was">{inr(order.original_amount)}</s>} {inr(order.amount)}</strong>
      </div>
    </>
  );
}

function PayForm({ sessionId, order, info, nav }) {
  const [txn, setTxn] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async e => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await axios.post(`${API}/payments/${sessionId}/submit`, { transaction_id: txn });
      nav(`/payment/success?session_id=${sessionId}`);
    } catch (err) {
      setError(errMsg(err));
      setBusy(false);
    }
  };
  return (
    <form onSubmit={submit} data-testid="pay-form">
      <PayDetails order={order} info={info} />
      <label>Transaction ID / UTR<input required minLength={6} maxLength={40} value={txn} onChange={e => setTxn(e.target.value)} placeholder="e.g. 412345678901" data-testid="pay-transaction-input" /></label>
      {error && <p className="form-error" data-testid="pay-error">{error}</p>}
      <button className="dark-button full" disabled={busy} data-testid="pay-submit-button">{busy ? "Sending…" : "I've paid, confirm my order"}<ArrowUpRight size={16} /></button>
      <small className="checkout-fine">The owner checks each payment, usually within a few hours.</small>
    </form>
  );
}

export default function PayPage() {
  const { sessionId } = useParams();
  const nav = useNavigate();
  const { order, info, missing } = usePayOrder(sessionId, nav);
  if (missing) return <NotFound what="order" />;
  if (!order || !info) return <Loading text="Loading payment details…" />;
  return (
    <>
      <Header />
      <main className="checkout pay-page">
        <div className="checkout-panel">
          <PayInstructions order={order} />
          <PayForm sessionId={sessionId} order={order} info={info} nav={nav} />
        </div>
      </main>
    </>
  );
}
