import { useEffect, useState } from "react";
import axios from "axios";
import { ArrowUpRight, Check, Copy, Sparkles, X } from "lucide-react";
import { API, logWarn } from "@/lib/store";

const hideKey = code => `promo-hide-${code}`;

export function PromoBanner() {
  const [promo, setPromo] = useState(null);
  const [hidden, setHidden] = useState(false);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    axios.get(`${API}/store/promo`)
      .then(r => { if (r.data && sessionStorage.getItem(hideKey(r.data.code)) !== "1") setPromo(r.data); })
      .catch(logWarn("Promo banner unavailable"));
  }, []);
  if (!promo || hidden) return null;
  const copy = () => { navigator.clipboard?.writeText(promo.code); setCopied(true); setTimeout(() => setCopied(false), 1800); };
  const close = () => { sessionStorage.setItem(hideKey(promo.code), "1"); setHidden(true); };
  return (
    <div className="promo-banner" data-testid="promo-banner">
      <div className="promo-inner">
        <span className="promo-spark"><Sparkles size={14} /> FESTIVE LAUNCH</span>
        <p>
          <b data-testid="promo-percent">{promo.percent}% off</b> everything with code{" "}
          <button className="promo-code" onClick={copy} title="Copy code" data-testid="promo-code-button">{promo.code}{copied ? <Check size={13} /> : <Copy size={13} />}</button>
          {promo.remaining != null && <span className="promo-left" data-testid="promo-remaining"> · only {promo.remaining} left</span>}
        </p>
        <a href="/#shop" className="promo-cta" data-testid="promo-shop-link">Shop the sale <ArrowUpRight size={13} /></a>
        <button className="promo-close" onClick={close} aria-label="Dismiss" data-testid="promo-close-button"><X size={15} /></button>
      </div>
      <small className="promo-note">Applied automatically at checkout</small>
    </div>
  );
}
