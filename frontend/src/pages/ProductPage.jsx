import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowUpRight, Eye, Lock } from "lucide-react";
import { imgFallback, priceText } from "@/lib/store";
import { useProduct } from "@/hooks/useProduct";
import { Header, Loading, NotFound } from "@/components/store/Header";
import { PromoBanner } from "@/components/store/PromoBanner";
import { WorkbookPreview } from "@/components/store/Modals";

function DetailCopy({ p }) {
  const free = p.price === 0;
  return (
    <div className="detail-copy">
      <p className="eyebrow">{p.category} · {p.tag}</p>
      <h1>{p.name}</h1>
      <p className="detail-description">{p.description}</p>
      <div className="price-row">
        <strong data-testid="product-detail-price">{priceText(p)}</strong>
        <span>{free ? "Instant download · No payment needed" : "Digital download · Pay with GPay / UPI"}</span>
      </div>
      {p.file_uploaded ? (
        <>
          <Link to={`/checkout/${p.id}`} className="dark-button full" data-testid="buy-product-button">{free ? "Get the free template" : "Get the download"} <ArrowUpRight size={16} /></Link>
          <div className="secure-note"><Lock size={16} /> {free ? "Delivered to your email instantly" : "Private delivery once payment is confirmed"}</div>
        </>
      ) : (
        <p className="form-error" data-testid="product-file-unavailable">This download is being prepared. Please check back soon.</p>
      )}
    </div>
  );
}

export default function ProductPage() {
  const { id } = useParams();
  const { product: p, missing } = useProduct(id);
  const [preview, setPreview] = useState(false);
  if (missing) return <NotFound what="product" />;
  if (!p) return <Loading text="Loading the good stuff…" />;
  return (
    <>
      {p.price > 0 && <PromoBanner />}
      <Header />
      <main className="detail">
        <Link to="/" className="back-link" data-testid="product-back-link">← Back to collection</Link>
        <div className="detail-grid">
          <div className="detail-image-wrap">
            <img src={p.image_url || imgFallback} alt={p.name} data-testid="product-detail-image" />
            <button className="preview-button" onClick={() => setPreview(true)} data-testid="open-workbook-preview"><Eye size={15} /> See inside</button>
          </div>
          <DetailCopy p={p} />
        </div>
      </main>
      {preview && <WorkbookPreview product={p} onClose={() => setPreview(false)} />}
    </>
  );
}
