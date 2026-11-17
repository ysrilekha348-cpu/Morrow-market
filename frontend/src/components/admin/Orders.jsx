import { useState } from "react";
import axios from "axios";
import { Check, Mail, ShoppingBag, Tag, X } from "lucide-react";
import { API, STATUS_LABEL, errMsg, inr } from "@/lib/store";

const FILTERS = [["all", "All orders"], ["pending_review", "Needs review"], ["paid", "Confirmed"], ["rejected", "Rejected"]];
const EMAIL_LABEL = { sent: "Emailed", failed: "Retry email" };

function OrderFilters({ value, onChange }) {
  return (
    <div className="order-filters" data-testid="order-filters">
      {FILTERS.map(([key, label]) => <button key={key} className={value === key ? "active" : ""} onClick={() => onChange(key)} data-testid={`order-filter-${key}`}>{label}</button>)}
    </div>
  );
}

function ReviewButtons({ o, busy, act }) {
  return (
    <>
      <button className="icon-button approve" disabled={busy} onClick={() => act("approve")} title="Approve" data-testid={`approve-order-${o.id}`}><Check size={17} /></button>
      <button className="icon-button reject" disabled={busy} onClick={() => act("reject")} title="Reject" data-testid={`reject-order-${o.id}`}><X size={17} /></button>
    </>
  );
}

function EmailButton({ o, busy, act }) {
  const title = o.email_status === "failed" ? `${o.email_error || "Email failed"}. Tap to retry.` : "Send the download email again";
  return (
    <button className={`email-chip ${o.email_status || "none"}`} disabled={busy} onClick={() => act("resend-email")} title={title} data-testid={`resend-email-${o.id}`}>
      <Mail size={13} /> {busy ? "Sending…" : EMAIL_LABEL[o.email_status] || "Send email"}
    </button>
  );
}

function OrderMeta({ o }) {
  return (
    <div>
      <b>{o.product_name}</b>
      <span>
        {o.customer_email}
        {o.discount_code && <> · <Tag size={11} /> {o.discount_code} −{o.discount_percent}%</>}
        {o.transaction_id && <> · UTR <code data-testid={`order-utr-${o.id}`}>{o.transaction_id}</code></>}
      </span>
    </div>
  );
}

function OrderRow({ o, auth, onDone }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const act = async action => {
    setBusy(true);
    setErr("");
    try {
      await axios.post(`${API}/admin/orders/${o.id}/${action}`, {}, await auth());
      onDone();
    } catch (e) {
      setErr(errMsg(e));
    }
    setBusy(false);
  };
  return (
    <div className="admin-row order" data-testid={`admin-order-${o.id}`}>
      <OrderMeta o={o} />
      <span className={`status ${o.payment_status}`} data-testid={`order-status-${o.id}`}>{STATUS_LABEL[o.payment_status] || o.payment_status}</span>
      <strong>{inr(o.amount)}</strong>
      <div className="order-actions">
        {o.payment_status === "pending_review" && <ReviewButtons o={o} busy={busy} act={act} />}
        {o.payment_status === "paid" && <EmailButton o={o} busy={busy} act={act} />}
        {err && <small className="form-error" data-testid={`order-error-${o.id}`}>{err}</small>}
      </div>
    </div>
  );
}

export function OrdersSection({ orders, auth, onDone }) {
  const [filter, setFilter] = useState("all");
  const visible = filter === "all" ? orders : orders.filter(o => o.payment_status === filter);
  return (
    <section className="admin-section">
      <div className="section-label"><ShoppingBag size={18} /><h2>Orders</h2></div>
      <OrderFilters value={filter} onChange={setFilter} />
      <div className="admin-list">
        {visible.length
          ? visible.map(o => <OrderRow key={o.id} o={o} auth={auth} onDone={onDone} />)
          : <p className="empty">{filter === "all" ? "Orders will appear here after your first sale." : "No orders in this view."}</p>}
      </div>
    </section>
  );
}
