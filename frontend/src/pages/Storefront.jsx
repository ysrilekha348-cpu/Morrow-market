import { useEffect, useState } from "react";
import axios from "axios";
import { ArrowUpRight, Search } from "lucide-react";
import { API, imgFallback, logWarn } from "@/lib/store";
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

function Filters({ cats, category, setCategory, query, setQuery }) {
  return (
    <div className="filter-row">
      <div className="pills">
        {cats.map(c => (
          <button key={c} className={category === c ? "pill active" : "pill"} onClick={() => setCategory(c)} data-testid={`category-${c.toLowerCase().replace(/\s+/g, "-")}`}>{c}</button>
        ))}
      </div>
      <label className="search"><Search size={16} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search the collection" data-testid="product-search-input" /></label>
    </div>
  );
}

function Shop() {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  useEffect(() => { axios.get(`${API}/products`).then(r => setProducts(r.data)).catch(logWarn("Products failed to load")); }, []);
  const cats = ["All", ...new Set(products.map(p => p.category))];
  const shown = products.filter(p => (category === "All" || p.category === category) && p.name.toLowerCase().includes(query.toLowerCase()));
  return (
    <section id="shop" className="shop-section">
      <div className="section-head">
        <div><p className="eyebrow">THE COLLECTION</p><h2>Digital goods<br /><i>with intention.</i></h2></div>
        <p className="section-blurb">Small tools can make a surprisingly big difference. Start with the thing that meets you where you are.</p>
      </div>
      <Filters cats={cats} category={category} setCategory={setCategory} query={query} setQuery={setQuery} />
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
