import { useState } from "react";
import axios from "axios";
import { Package, UploadCloud } from "lucide-react";
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
  };
  return (
    <label className="outline-button small" title={state || "Upload the file customers receive"} data-testid={`upload-file-${product.id}`}>
      <UploadCloud size={15} /> {state || (product.file_uploaded ? "Replace file" : "Upload real file")}
      <input type="file" hidden onChange={upload} data-testid={`upload-file-input-${product.id}`} />
    </label>
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
      <input required type="number" min="1" step=".01" placeholder="Price (₹)" {...field("price")} data-testid="new-product-price" />
      <input placeholder="Category" {...field("category")} data-testid="new-product-category" />
      <input placeholder="Cover image URL (optional)" {...field("image_url")} data-testid="new-product-image" />
      {err && <p className="form-error" data-testid="add-product-error">{err}</p>}
      <button className="dark-button" disabled={saving} data-testid="save-product-button">{saving ? "Saving…" : "Save product"}</button>
    </form>
  );
}

export function ProductsSection({ products, auth, onDone }) {
  return (
    <section className="admin-section">
      <div className="section-label"><Package size={18} /><h2>Products</h2></div>
      <div className="admin-list">
        {products.map(p => (
          <div className="admin-row" key={p.id} data-testid={`admin-product-${p.id}`}>
            <img src={p.image_url || imgFallback} alt="" />
            <div><b>{p.name}</b><span>{p.category} · {p.published ? "Published" : "Draft"} · {p.file_uploaded ? `File uploaded: ${p.file_name}` : "Real download file required"}</span></div>
            <strong>{inr(p.price)}</strong>
            <FileUpload product={p} auth={auth} onDone={onDone} />
          </div>
        ))}
      </div>
    </section>
  );
}
