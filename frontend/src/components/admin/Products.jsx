import { useState } from "react";
import axios from "axios";
import { Check, Package, Pencil, UploadCloud, X } from "lucide-react";
import { API, errMsg, imgFallback, inr } from "@/lib/store";

const emptyForm = { name: "", description: "", price: "", category: "Guides", tag: "New", image_url: "", published: true };

function FileUpload({ product, auth, onDone }) {
  const [state, setState] = useState("");
  const upload = async e => {
    const f = e.target.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    setState("Uploading…");
    try { await axios.post(`${API}/admin/products/${product.id}/file`, fd, await auth()); setState(""); onDone(); }
    catch (err) { setState(errMsg(err)); }
    e.target.value = "";
  };
  return (
    <label className="outline-button small" title={state || "Upload the file customers receive"} data-testid={`upload-file-${product.id}`}>
      <UploadCloud size={15} /> {state || (product.file_uploaded ? "Replace file" : "Upload real file")}
      <input type="file" hidden onChange={upload} data-testid={`upload-file-input-${product.id}`} />
    </label>
  );
}

function ProductEditor({ product, auth, onDone, onCancel }) {
  const [form, setForm] = useState({
    name: product.name || "", description: product.description || "", price: String(product.price ?? ""),
    category: product.category || "Guides", tag: product.tag || "New", image_url: product.image_url || "",
    published: Boolean(product.published),
  });
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  const field = key => ({ value: form[key], onChange: e => setForm({ ...form, [key]: e.target.value }) });
  const save = async e => {
    e.preventDefault();
    setSaving(true);
    setErr("");
    try {
      await axios.patch(`${API}/admin/products/${product.id}`, { ...form, price: Number(form.price) }, await auth());
      onDone();
    } catch (error) {
      setErr(errMsg(error));
      setSaving(false);
    }
  };
  return (
    <form className="admin-form product-editor" onSubmit={save} data-testid={`edit-product-form-${product.id}`}>
      <input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Product name" aria-label="Product name" />
      <textarea required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Description" aria-label="Product description" />
      <div className="editor-fields">
        <input required type="number" min="0" step=".01" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} placeholder="Price (₹)" aria-label="Price" />
        <input value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} placeholder="Category" aria-label="Category" />
        <input value={form.tag} onChange={e => setForm({ ...form, tag: e.target.value })} placeholder="Product tag" aria-label="Product tag" />
        <input value={form.image_url} onChange={e => setForm({ ...form, image_url: e.target.value })} placeholder="Cover image URL" aria-label="Cover image URL" />
      </div>
      <label className="publish-toggle"><input type="checkbox" checked={form.published} onChange={e => setForm({ ...form, published: e.target.checked })} /> Published in storefront</label>
      {err && <p className="form-error" role="alert">{err}</p>}
      <div className="settings-actions">
        <button className="dark-button" disabled={saving} data-testid={`save-product-edit-${product.id}`}><Check size={15} /> {saving ? "Saving…" : "Save changes"}</button>
        <button type="button" className="outline-button" onClick={onCancel}><X size={15} /> Cancel</button>
      </div>
    </form>
  );
}

export function AddProductForm({ auth, onSaved }) {
  const [form, setForm] = useState(emptyForm);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  const field = key => ({ value: form[key], onChange: e => setForm({ ...form, [key]: e.target.value }) });
  const add = async e => {
    e.preventDefault();
    setSaving(true);
    setErr("");
    try {
      await axios.post(`${API}/admin/products`, { ...form, price: Number(form.price) }, await auth());
      setForm(emptyForm);
      onSaved();
    } catch (error) {
      setErr(errMsg(error));
    }
    setSaving(false);
  };
  return (
    <form className="admin-form" onSubmit={add} data-testid="add-product-form">
      <input required placeholder="Product name" {...field("name")} data-testid="new-product-name" />
      <textarea required placeholder="Short description" {...field("description")} data-testid="new-product-description" />
      <input required type="number" min="0" step=".01" placeholder="Price (₹)" {...field("price")} data-testid="new-product-price" />
      <input placeholder="Category" {...field("category")} data-testid="new-product-category" />
      <input placeholder="Cover image URL (optional)" {...field("image_url")} data-testid="new-product-image" />
      {err && <p className="form-error" data-testid="add-product-error">{err}</p>}
      <button className="dark-button" disabled={saving} data-testid="save-product-button">{saving ? "Saving…" : "Save product"}</button>
    </form>
  );
}

export function ProductsSection({ products, auth, onDone }) {
  const [editing, setEditing] = useState("");
  return (
    <section className="admin-section">
      <div className="section-label"><Package size={18} /><h2>Products</h2></div>
      <div className="admin-list">
        {products.map(p => (
          <div className="product-admin-item" key={p.id} data-testid={`admin-product-${p.id}`}>
            <div className="admin-row">
              <img src={p.image_url || imgFallback} alt="" />
              <div><b>{p.name}</b><span>{p.category} · {p.published ? "Published" : "Draft"} · {p.file_uploaded ? `File uploaded: ${p.file_name}` : "Real download file required"}</span></div>
              <strong>{inr(p.price)}</strong>
              <div className="product-admin-actions">
                <button type="button" className="outline-button small" onClick={() => setEditing(editing === p.id ? "" : p.id)} data-testid={`edit-product-${p.id}`}><Pencil size={14} /> Edit</button>
                <FileUpload product={p} auth={auth} onDone={onDone} />
              </div>
            </div>
            {editing === p.id && <ProductEditor product={p} auth={auth} onDone={() => { setEditing(""); onDone(); }} onCancel={() => setEditing("")} />}
          </div>
        ))}
      </div>
    </section>
  );
}
