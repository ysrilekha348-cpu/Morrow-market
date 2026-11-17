import { useEffect, useState } from "react";
import { ClerkProvider } from "@clerk/react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const MAX_TRIES = 10;
const appearance = { variables: { colorPrimary: "#29352f", colorBackground: "#f5f4ef", colorForeground: "#29352f", fontFamily: "DM Sans" } };

function useClerkConfig() {
  const [config, setConfig] = useState(null);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let stopped = false;
    const load = async (n = 0) => {
      try {
        const r = await fetch(`${BACKEND_URL}/api/clerk/config`);
        const c = await r.json();
        if (c.enabled && !stopped) { setConfig(c); return; }
      } catch (e) {
        console.warn("Clerk configuration request failed", e);
      }
      if (stopped) return;
      if (n < MAX_TRIES) setTimeout(() => load(n + 1), 1200);
      else setUnavailable(true);
    };
    load();
    return () => { stopped = true; };
  }, []);
  return { config, unavailable };
}

export default function ClerkAuthProvider({ children }) {
  const { config, unavailable } = useClerkConfig();
  if (unavailable) return <div className="loading">Sign-in is unavailable right now. Please refresh and try again.</div>;
  if (!config) return <div className="loading">Opening Morrow market…</div>;
  return (
    <ClerkProvider publishableKey={config.publishable_key} proxyUrl={config.proxy_url || undefined} appearance={appearance}
      signInUrl="/sign-in" signUpUrl="/sign-up" signInFallbackRedirectUrl="/" signUpFallbackRedirectUrl="/" afterSignOutUrl="/">
      {children}
    </ClerkProvider>
  );
}
