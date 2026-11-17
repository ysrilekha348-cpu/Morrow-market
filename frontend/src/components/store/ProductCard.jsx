import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Eye, Heart } from "lucide-react";
import { imgFallback, priceText } from "@/lib/store";
import { QuickView } from "@/components/store/Modals";

const likeKey = id => `morrow-like-${id}`;

export function ProductCard({ product, index }) {
  const [quick, setQuick] = useState(false);
  const [liked, setLiked] = useState(() => localStorage.getItem(likeKey(product.id)) === "1");
  const toggleLike = () => { const next = !liked; setLiked(next); localStorage.setItem(likeKey(product.id), next ? "1" : "0"); };
  return (
    <>
      <article className={`product-card card-${index % 3}`} data-testid={`product-card-${product.id}`}>
        <div className="product-image">
          <Link to={`/product/${product.id}`} data-testid={`product-link-${product.id}`}>
            <img src={product.image_url || imgFallback} alt={product.name} />
            <span className="tag">{product.price === 0 ? "Free template" : product.tag}</span>
          </Link>
          <div className="card-actions">
            <button className={`card-icon ${liked ? "liked" : ""}`} onClick={toggleLike} aria-label="Save product" data-testid={`save-product-${product.id}`}><Heart size={16} fill={liked ? "currentColor" : "none"} /></button>
            <button className="card-icon" onClick={() => setQuick(true)} aria-label="Quick view" data-testid={`quick-view-${product.id}`}><Eye size={16} /></button>
          </div>
          <Link to={`/product/${product.id}`} className="view-arrow" data-testid={`view-product-${product.id}`}><ArrowUpRight size={18} /></Link>
        </div>
        <div className="product-info">
          <div><p className="product-category">{product.category}</p><h3>{product.name}</h3></div>
          <strong data-testid={`product-price-${product.id}`}>{priceText(product)}</strong>
        </div>
        <p className="product-description">{product.description}</p>
      </article>
      {quick && <QuickView product={product} onClose={() => setQuick(false)} />}
    </>
  );
}
