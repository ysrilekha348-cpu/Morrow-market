import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, ChevronLeft, ChevronRight, X } from "lucide-react";
import { imgFallback, priceText } from "@/lib/store";
import { previewText } from "@/lib/previewText";

export function Modal({ children, onClose, label }) {
  const slug = label.toLowerCase().replaceAll(" ", "-");
  return (
    <div className="modal-backdrop" role="dialog" aria-label={label} data-testid={`${slug}-modal`} onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <button className="modal-close" onClick={onClose} aria-label="Close" data-testid={`${slug}-close`}><X size={17} /></button>
        {children}
      </div>
    </div>
  );
}

export function QuickView({ product, onClose }) {
  return (
    <Modal label="Quick view" onClose={onClose}>
      <div className="quick-grid">
        <img src={product.image_url || imgFallback} alt={product.name} />
        <div>
          <p className="eyebrow">{product.category} · {product.tag}</p>
          <h2>{product.name}</h2>
          <p className="quick-description">{product.description}</p>
          <strong className="quick-price">{priceText(product)}</strong>
          <Link to={`/product/${product.id}`} onClick={onClose} className="dark-button full" data-testid={`quick-view-open-${product.id}`}>
            {product.price === 0 ? "Get the free template" : "See the full workbook"}<ArrowUpRight size={15} />
          </Link>
        </div>
      </div>
    </Modal>
  );
}

const PAGE_HINTS = ["A prompt to begin", "Space for your thoughts", "A page to return to"];

export function WorkbookPreview({ product, onClose }) {
  const [page, setPage] = useState(0);
  const copy = previewText(product);
  return (
    <Modal label="Workbook preview" onClose={onClose}>
      <div className="preview-head">
        <div><p className="eyebrow">A little peek inside</p><h2>{product.name}</h2></div>
        <span data-testid="preview-page-indicator">{page + 1} / 3</span>
      </div>
      <div className="preview-stage">
        <button className="preview-arrow left" disabled={!page} onClick={() => setPage(page - 1)} data-testid="preview-previous-button"><ChevronLeft size={16} /></button>
        <div className="preview-sheet">
          <span className="preview-number">0{page + 1}</span>
          <p className="eyebrow">{product.category}</p>
          <h3>{copy[page]}</h3>
          <div className="preview-lines"><i></i><i></i><i></i><i></i></div>
          <small>{PAGE_HINTS[page]}</small>
        </div>
        <button className="preview-arrow" disabled={page === 2} onClick={() => setPage(page + 1)} data-testid="preview-next-button"><ChevronRight size={17} /></button>
      </div>
      <Link to={`/checkout/${product.id}`} onClick={onClose} className="dark-button full" data-testid="preview-cta">
        {product.price === 0 ? "Get this free template" : "Get the full workbook"}<ArrowUpRight size={15} />
      </Link>
    </Modal>
  );
}
