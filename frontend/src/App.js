import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { SignIn, SignUp } from "@clerk/react";
import "@/App.css";
import ClerkAuthProvider from "@/components/auth/ClerkAuthProvider";
import Storefront from "@/pages/Storefront";
import ProductPage from "@/pages/ProductPage";
import Checkout from "@/pages/Checkout";
import PayPage from "@/pages/PayPage";
import Success from "@/pages/Success";
import Admin from "@/pages/Admin";

function AuthPage({ signup = false }) {
  return (
    <div className="auth-page">
      <Link to="/" className="brand" data-testid="auth-brand-link"><span className="brand-mark">M</span> Morrow <em>market</em></Link>
      <div className="auth-card">
        {signup ? <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" /> : <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" withSignUp />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ClerkAuthProvider>
        <Routes>
          <Route path="/" element={<Storefront />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/checkout/:id" element={<Checkout />} />
          <Route path="/pay/:sessionId" element={<PayPage />} />
          <Route path="/payment/success" element={<Success />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/sign-in/*" element={<AuthPage />} />
          <Route path="/sign-up/*" element={<AuthPage signup />} />
        </Routes>
      </ClerkAuthProvider>
    </BrowserRouter>
  );
}
