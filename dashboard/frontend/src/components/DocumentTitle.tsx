import { useEffect } from "react";
import { useLocation } from "react-router";
import { PAGE_META } from "../data/humanize";

const BRAND = "QuantSilico // Everesteer 2026";

/** Keep the browser tab title aligned with the active console route. */
export default function DocumentTitle() {
  const { pathname } = useLocation();

  useEffect(() => {
    const meta = PAGE_META[pathname];
    document.title = meta ? `${meta.title} — ${BRAND}` : `${BRAND} — Research Console`;
  }, [pathname]);

  return null;
}
