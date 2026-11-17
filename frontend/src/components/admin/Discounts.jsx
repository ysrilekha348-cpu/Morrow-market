import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { Megaphone, Plus, Tag } from "lucide-react";
import { API, errMsg, logWarn } from "@/lib/store";

const emptyCode = { code: "", percent: "", max_uses: "" };

function DiscountForm({ auth, onCreated, setMsg }) {
  const [f, setF] = useState(emptyCode);
  const [busy, setBusy] = useState(false);
  const create = async e => {
    e.preventDefault();
    setBusy(true);
    setMsg("");
    try {
      await axios.post(`${API}/admin/discounts`, { code: f.code, percent: Number(f.percent), max_uses: f.max_uses ? Number(f.max_uses) : null }, await auth());
      setF(emptyCode);
      setMsg("Code created");
      onCreated();
    } catch (err) {
      setMsg(errMsg(err));
    }
    setBusy(false);
  };
  return (
    <form className="discount-form" onSubmit={create} data-testid="discount-form">
      <input required minLength={3} maxLength={24} pattern="[A-Za-z0-9_\-]+" placeholder="CODE e.g. DIWALI20" value={f.code} onChange={e => setF({ ...f, code: e.target.value.toUpperCase() })} data-testid="new-discount-code" />
      <input required type="number" min="1" max="95" placeholder="% off" value={f.percent} onChange={e => setF({ ...f, percent: e.target.value })} data-testid="new-discount-percent" />
      <input type="number" min="1" placeholder="Max uses (blank = unlimited)" value={f.max_uses} onChange={e => setF({ ...f, max_uses: e.target.value })} data-testid="new-discount-max-uses" />
      <button className="dark-button" disabled={busy} data-testid="create-discount-button"><Plus size={15} /> Create code</button>
    </form>
  );
}

function DiscountRow({ d, toggle }) {
  const used = d.max_uses && d.uses >= d.max_uses;
  const live = d.active && !used;
  return (
    <div className="admin-row discount" data-testid={`discount-row-${d.code}`}>
      <div>
        <b className="code-name">{d.code}</b>
        <span>
          {d.percent}% off · used {d.uses}{d.max_uses ? ` / ${d.max_uses}` : " (no limit)"}
          {d.featured && <em className="on-banner" data-testid={`discount-featured-${d.code}`}> · <Megaphone size={11} /> On store banner</em>}
        </span>
      </div>
      <span className={`status ${live ? "paid" : "awaiting_payment"}`} data-testid={`discount-status-${d.code}`}>{!d.active ? "Paused" : used ? "Used up" : "Live"}</span>
      <div className="discount-actions">
        <button className="outline-button small" onClick={() => toggle(d, { featured: !d.featured })} data-testid={`discount-feature-${d.code}`}>{d.featured ? "Hide banner" : "Show on banner"}</button>
        <button className="outline-button small" onClick={() => toggle(d, { active: !d.active })} data-testid={`discount-toggle-${d.code}`}>{d.active ? "Pause" : "Resume"}</button>
      </div>
    </div>
  );
}

export function Discounts({ auth }) {
  const [list, setList] = useState([]);
  const [msg, setMsg] = useState("");
  const load = useCallback(async () => {
    const r = await axios.get(`${API}/admin/discounts`, await auth());
    setList(r.data);
  }, [auth]);
  useEffect(() => { load().catch(logWarn("Discount codes failed to load")); }, [load]);
  const toggle = async (d, changes) => {
    try { await axios.patch(`${API}/admin/discounts/${d.id}`, changes, await auth()); load(); }
    catch (err) { setMsg(errMsg(err)); }
  };
  return (
    <section className="admin-section" data-testid="discounts-section">
      <div className="section-label"><Tag size={18} /><h2>Discount codes</h2></div>
      <DiscountForm auth={auth} onCreated={load} setMsg={setMsg} />
      {msg && <small className="settings-msg" data-testid="discount-message">{msg}</small>}
      <div className="admin-list">
        {list.length ? list.map(d => <DiscountRow key={d.id} d={d} toggle={toggle} />) : <p className="empty">Create a code like DIWALI20 to run a festive sale.</p>}
      </div>
    </section>
  );
}
