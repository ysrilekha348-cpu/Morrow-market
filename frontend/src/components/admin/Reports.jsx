import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { Archive, FileSpreadsheet, Mail, Sunrise } from "lucide-react";
import { API, errMsg, logWarn } from "@/lib/store";

const TIMES = [[7, "7 AM"], [8, "8 AM"], [9, "9 AM"], [0, "Off"]];

const saveBlob = (res, fallback) => {
  const name = /filename="([^"]+)"/.exec(res.headers["content-disposition"] || "")?.[1] || fallback;
  const url = URL.createObjectURL(res.data);
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  URL.revokeObjectURL(url);
};

function DownloadButton({ auth, path, fallback, icon: Icon, label, testId, setMsg }) {
  const [busy, setBusy] = useState(false);
  const go = async () => {
    setBusy(true);
    setMsg("");
    try { saveBlob(await axios.get(`${API}${path}`, { ...(await auth()), responseType: "blob" }), fallback); }
    catch (err) { setMsg("Download failed. Please try again."); logWarn("Download failed")(err); }
    setBusy(false);
  };
  return <button className="outline-button" onClick={go} disabled={busy} data-testid={testId}><Icon size={16} /> {busy ? "Preparing…" : label}</button>;
}

function SummarySettings({ auth, setMsg }) {
  const [s, setS] = useState(null);
  const [sending, setSending] = useState(false);
  const load = useCallback(async () => setS((await axios.get(`${API}/admin/reports/settings`, await auth())).data), [auth]);
  useEffect(() => { load().catch(logWarn("Summary settings failed to load")); }, [load]);
  if (!s) return null;
  const choose = async hour => {
    try { setS((await axios.put(`${API}/admin/reports/settings`, { summary_hour: hour }, await auth())).data); setMsg(hour ? `Morning summary set for ${hour} AM India time` : "Morning summary turned off"); }
    catch (err) { setMsg(errMsg(err)); }
  };
  const sendNow = async () => {
    setSending(true);
    try { setS((await axios.post(`${API}/admin/reports/send-summary`, {}, await auth())).data); setMsg(`Summary sent to ${s.recipient}`); }
    catch (err) { setMsg(errMsg(err)); }
    setSending(false);
  };
  return (
    <div className="summary-settings" data-testid="summary-settings">
      <div><b><Sunrise size={15} /> Morning sales email</b><span>Overnight sales, free downloads and payments waiting for you, sent to {s.recipient}{s.last_sent_on && ` · last sent ${s.last_sent_on}`}</span></div>
      <div className="order-filters" data-testid="summary-time-options">
        {TIMES.map(([h, label]) => <button key={h} className={s.summary_hour === h ? "active" : ""} onClick={() => choose(h)} data-testid={`summary-time-${h || "off"}`}>{label}</button>)}
      </div>
      <button className="outline-button small" onClick={sendNow} disabled={sending} data-testid="send-summary-now"><Mail size={14} /> {sending ? "Sending…" : "Send me one now"}</button>
    </div>
  );
}

export function Reports({ auth }) {
  const [msg, setMsg] = useState("");
  return (
    <section className="admin-section" data-testid="reports-section">
      <div className="section-label"><Archive size={18} /><h2>Reports & exports</h2></div>
      <div className="settings-actions report-actions">
        <DownloadButton auth={auth} path="/admin/orders/spreadsheet" fallback="orders.xlsx" icon={FileSpreadsheet} label="Orders spreadsheet" testId="download-orders-spreadsheet" setMsg={setMsg} />
        <DownloadButton auth={auth} path="/admin/export" fallback="export.zip" icon={Archive} label="Export all data" testId="export-all-data" setMsg={setMsg} />
      </div>
      <SummarySettings auth={auth} setMsg={setMsg} />
      {msg && <small className="settings-msg" data-testid="reports-message">{msg}</small>}
    </section>
  );
}
