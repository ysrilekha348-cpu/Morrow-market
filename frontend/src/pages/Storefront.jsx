import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { ArrowUpRight, Search } from "lucide-react";
import { API, imgFallback } from "@/lib/store";
import { Header } from "@/components/store/Header";
import { PromoBanner } from "@/components/store/PromoBanner";
import { ProductCard } from "@/components/store/ProductCard";

function Hero() {
  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">CURATED DIGITAL GOODS</p>
        <h1>Make room for<br /><i>better work.</i></h1>
        <p className="hero-lede">Thoughtful templates, guides, and systems for building a life and business that feels like yours.</p>
        <a href="#shop" className="dark-button" data-testid="hero-shop-button">Explore the collection <ArrowUpRight size={16} /></a>
      </div>
      <div className="hero-art">
        <img src={imgFallback} alt="Notebook and creative desk" data-testid="hero-image" />
        <span className="hero-note">Made for your<br /><i>next chapter</i></span>
      </div>
    </section>
  );
}

function Filters({ cats, category, setCategory, query, setQuery, sort, setSort }) {
  return (
    <div className="filter-row">
      <div className="pills">
        {cats.map(c => (
          <button key={c} className={category === c ? "pill active" : "pill"} onClick={() => setCategory(c)} data-testid={`category-${c.toLowerCase().replace(/\\s+/g, "-")}`}>{c}</button>
        ))}
      </div>
      <label className="search"><Search size={16} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search name, category or details" aria-label="Search products" data-testid="product-search-input" /></label>
      <label className="sort-control"><span>Sort</span><select value={sort} onChange={e => setSort(e.target.value)} aria-label="Sort products" data-testid="product-sort">
        <option value="featured">Featured</option>
        <option value="price-asc">Price: low to high</option>
        <option value="price-desc">Price: high to low</option>
        <option value="name">Name: A to Z</option>
      </select></label>
    </div>
  );
}

function Shop() {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("featured");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    axios.get(`${API}/products`)
      .then(r => { if (active) setProducts(Array.isArray(r.data) ? r.data : []); })
      .catch(() => { if (active) setError("We couldn't load the collection. Please try again."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const cats = ["All", ...new Set(products.map(p => p.category).filter(Boolean))];
  const shown = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = products.filter(p => {
      const matchesCategory = category === "All" || p.category === category;
      const searchable = [p.name, p.category, p.description, p.tag].filter(Boolean).join(" ").toLowerCase();
      return matchesCategory && (!needle || searchable.includes(needle));
    });
    if (sort === "price-asc") filtered.sort((a, b) => Number(a.price) - Number(b.price));
    if (sort === "price-desc") filtered.sort((a, b) => Number(b.price) - Number(a.price));
    if (sort === "name") filtered.sort((a, b) => a.name.localeCompare(b.name));
    return filtered;
  }, [products, category, query, sort]);

  const reset = () => { setCategory("All"); setQuery(""); setSort("featured"); };

  return (
    <section id="shop" className="shop-section">
      <div className="section-head">
        <div><p className="eyebrow">THE COLLECTION</p><h2>Digital goods<br /><i>with intention.</i></h2></div>
        <p className="section-blurb">Small tools can make a surprisingly big difference. Start with the thing that meets you where you are.</p>
      </div>
      <Filters cats={cats} category={category} setCategory={setCategory} query={query} setQuery={setQuery} sort={sort} setSort={setSort} />
      {loading && <p className="collection-message" role="status" data-testid="products-loading">Loading the collection…</p>}
      {error && <div className="collection-message collection-error" role="alert" data-testid="products-error">{error} <button onClick={() => window.location.reload()}>Reload page</button></div>}
      {!loading && !error && shown.length > 0 && <p className="results-count" aria-live="polite">{shown.length} {shown.length === 1 ? "product" : "products"}</p>}
      {!loading && !error && shown.length === 0 && (
        <div className="collection-message" data-testid="products-empty">
          <h3>No products found</h3>
          <p>Try another search or clear your filters to see the full collection.</p>
          <button className="outline-button" onClick={reset} data-testid="clear-product-filters">Clear filters</button>
        </div>
      )}
      <div className="product-grid">{shown.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}</div>
    </section>
  );
}

export default function Storefront() {
  return (
    <>
      <PromoBanner />
      <Header />
      <main>
        <Hero />
        <section className="intro-band"><p>NOT MORE NOISE.</p><p>JUST THE GOOD STUFF.</p><span>↓</span></section>
        <Shop />
        <section id="about" className="manifesto">
          <div className="manifesto-number">01</div>
          <div><p className="eyebrow">A NOTE FROM MORROW</p><h2>Useful can<br /><i>still be beautiful.</i></h2></div>
          <p>Everything here is made to be opened, used, scribbled on, and returned to. No hustle theatre. No endless funnels. Just well-made digital things that help you move forward.</p>
        </section>
      </main>
      <footer><span>© MORROW MARKET</span><span>Made for the in-between moments</span><span>↓ KEEP EXPLORING</span></footer>
    </>
  );
}
