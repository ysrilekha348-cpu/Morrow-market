import { useState } from "react";
import axios from "axios";
import { Tag } from "lucide-react";
import { API, errMsg } from "@/lib/store";

export function DiscountField({ productId, code, setCode, deal, setDeal }) {
  const [msg, setMsg] = useState("");
  const apply = async () => {
    if (!code.trim()) return;
    setMsg("");
    try {
      const r = await axios.post(`${API}/discounts/validate`, { code, product_id: productId });
      setDeal(r.data);
    } catch (err) {
      setDeal(null);
      setMsg(errMsg(err));
    }
  };
  const clear = () => { setDeal(null); setCode(""); setMsg(""); };
  const onKey = e => { if (e.key === "Enter") { e.preventDefault(); apply(); } };
  return (
    <>
      <label>Discount code (optional)</label>
      {deal ? (
        <div className="code-applied" data-testid="discount-applied">
          <span><Tag size={14} /> {deal.code} · {deal.percent}% off</span>
          <button type="button" className="text-button" onClick={clear} data-testid="discount-remove-button">Remove</button>
        </div>
      ) : (
        <div className="code-row">
          <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} onKeyDown={onKey} placeholder="e.g. DIWALI20" data-testid="discount-code-input" />
          <button type="button" className="outline-button" onClick={apply} data-testid="discount-apply-button">Apply</button>
        </div>
      )}
      {msg && <p className="form-error" data-testid="discount-error">{msg}</p>}
    </>
  );
}
