import { useEffect, useState } from "react";
import axios from "axios";
import { API } from "@/lib/store";

export function useProduct(id) {
  const [product, setProduct] = useState(null);
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    setProduct(null);
    setMissing(false);
    axios.get(`${API}/products/${id}`).then(r => setProduct(r.data)).catch(() => setMissing(true));
  }, [id]);
  return { product, missing };
}
