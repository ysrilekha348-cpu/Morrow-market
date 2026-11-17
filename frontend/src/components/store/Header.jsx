import { Link } from "react-router-dom";
import { Show, SignInButton, UserButton } from "@clerk/react";

export function Header() {
  return (
    <header className="topbar">
      <Link to="/" className="brand" data-testid="brand-link"><span className="brand-mark">M</span> Morrow <em>market</em></Link>
      <nav>
        <a href="/#shop" data-testid="shop-nav-link">Shop</a>
        <a href="/#about" data-testid="about-nav-link">About</a>
        <Link to="/admin" data-testid="owner-nav-link">Owner space</Link>
      </nav>
      <div className="header-actions">
        <Show when="signed-out"><SignInButton mode="redirect"><button className="text-button" data-testid="sign-in-button">Owner sign in</button></SignInButton></Show>
        <Show when="signed-in"><UserButton /></Show>
      </div>
    </header>
  );
}

export function NotFound({ what }) {
  return (
    <>
      <Header />
      <main className="success" data-testid="not-found">
        <p className="eyebrow">NOT FOUND</p>
        <h1>We couldn't find<br /><i>that {what}.</i></h1>
        <Link to="/" className="dark-button" data-testid="not-found-home">Back to the store</Link>
      </main>
    </>
  );
}

export const Loading = ({ text }) => <div className="loading">{text}</div>;
