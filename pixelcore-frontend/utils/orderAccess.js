// Device-bound guest access, matching the existing cart's local-storage trust boundary.
// Never put these tokens in links, logs, analytics, or server-rendered HTML.
const MAX_AGE = 30 * 24 * 60 * 60 * 1000;
const LIMIT = 20;
const orderIdPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const key = (slug) => `pixelcore-order-access:${slug}`;

function records(storage, slug, now) {
  try {
    const parsed = JSON.parse(storage.getItem(key(slug)) || "[]");
    return Array.isArray(parsed)
      ? parsed.filter(
          (row) =>
            orderIdPattern.test(row?.orderId) &&
            typeof row.token === "string" &&
            row.token.length >= 16 &&
            row.token.length <= 512 &&
            Number.isFinite(row.savedAt) &&
            now - row.savedAt < MAX_AGE &&
            row.savedAt <= now,
        )
      : [];
  } catch {
    return [];
  }
}

export function rememberOrderAccess(
  storage,
  slug,
  orderId,
  token,
  now = Date.now(),
) {
  if (
    !storage ||
    !slug ||
    !orderIdPattern.test(orderId) ||
    typeof token !== "string" ||
    token.length < 16 ||
    token.length > 512
  )
    return false;
  try {
    const rows = records(storage, slug, now).filter(
      (row) => row.orderId !== orderId,
    );
    storage.setItem(
      key(slug),
      JSON.stringify(
        [{ orderId, token, savedAt: now }, ...rows].slice(0, LIMIT),
      ),
    );
    return true;
  } catch {
    return false;
  } // Storage restrictions must never fail checkout.
}

export function readOrderAccess(storage, slug, orderId, now = Date.now()) {
  if (!storage || !orderIdPattern.test(orderId)) return "";
  const rows = records(storage, slug, now);
  try {
    storage.setItem(key(slug), JSON.stringify(rows));
  } catch {}
  return rows.find((row) => row.orderId === orderId)?.token || "";
}
