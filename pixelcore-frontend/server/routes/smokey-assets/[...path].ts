// The public asset bridge intentionally forwards no account cookies or authorization.
export default defineEventHandler(async (event) => {
  assertMethod(event, ["GET", "HEAD"]);
  const incoming = getRequestURL(event);
  const origin = new URL(useRuntimeConfig(event).smokeyAssetProxyOrigin);
  const target = new URL(incoming.pathname + incoming.search, origin);
  try {
    const response = await fetch(target, {
      method: event.method,
      redirect: "error",
      signal: AbortSignal.timeout(15000),
    });
    setResponseStatus(event, response.status);
    // Exclude hop-by-hop framing headers from the nested Nuxt development proxy.
    for (const header of [
      "content-type",
      "cache-control",
      "etag",
      "last-modified",
      "x-content-type-options",
    ]) {
      const value = response.headers.get(header);
      if (value) setHeader(event, header, value);
    }
    return event.method === "HEAD"
      ? ""
      : Buffer.from(await response.arrayBuffer());
  } catch {
    throw createError({
      statusCode: 502,
      statusMessage: "Smokey assets are unavailable",
    });
  }
});
