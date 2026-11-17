import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { QrCode, UploadCloud } from "lucide-react";
import { API, errMsg, logWarn } from "@/lib/store";

export function PaymentSettings({ auth }) {
  const [s, setS] = useState(null);
  const [num, setNum] = useState("");
  const [msg, setMsg] = useState("");
  const load = useCallback(async () => {
    const r = await axios.get(`${API}/admin/settings`, await auth());
    setS(r.data);
    setNum(r.data.gpay_number);
  }, [auth]);
  useEffect(() => { load().catch(logWarn("Payment settings failed to load")); }, [load]);
  if (!s) return null;
  const save = async e => {
    e.preventDefault();
    try { await axios.put(`${API}/admin/settings`, { gpay_number: num }, await auth()); setMsg("Saved"); load(); }
    catch (err) { setMsg(errMsg(err)); }
  };
  const upload = async e => {
    const f = e.target.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    setMsg("Uploading QR…");
    try { const r = await axios.post(`${API}/admin/settings/qr`, fd, await auth()); setS(r.data); setMsg("QR code updated"); }
    catch (err) { setMsg(errMsg(err)); }
  };
  return (
    <section className="admin-section" data-testid="payment-settings">
      <div className="section-label"><QrCode size={18} /><h2>GPay details</h2></div>
      <div className="settings-grid">
        <div className="qr-box small">
          {s.has_qr ? <img src={`${API}/store/qr?v=${s.qr_version}`} alt="Your GPay QR" data-testid="admin-qr-preview" /> : <div className="qr-empty"><QrCode size={28} /><span>No QR yet</span></div>}
        </div>
        <form onSubmit={save} className="settings-form">
          <label>GPay number / UPI ID<input value={num} onChange={e => setNum(e.target.value)} data-testid="gpay-number-input" /></label>
          <div className="settings-actions">
            <button className="dark-button" data-testid="save-gpay-button">Save number</button>
            <label className="outline-button" data-testid="upload-qr-button"><UploadCloud size={16} /> {s.has_qr ? "Replace QR" : "Upload QR"}<input type="file" accept="image/*" hidden onChange={upload} data-testid="upload-qr-input" /></label>
          </div>
          {msg && <small className="settings-msg" data-testid="settings-message">{msg}</small>}
        </form>
      </div>
    </section>
  );
}
