export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
export const imgFallback = "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=1000&q=85";
export const inr = n => `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
export const priceText = p => (p.price === 0 ? "Free" : inr(p.price));
export const STATUS_LABEL = { awaiting_payment: "Awaiting payment", pending_review: "Needs review", paid: "Paid", rejected: "Rejected" };
export const errMsg = e => e?.response?.data?.detail?.[0]?.msg || e?.response?.data?.detail || "Something went wrong. Please try again.";
export const logWarn = label => e => console.warn(label, e);
