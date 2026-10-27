const normalize = (value) => String(value ?? "").trim().toLowerCase();

export function matchesPosSearch(offering, query) {
  const text = normalize(query);
  if (!text) return true;
  return [
    offering.name, offering.category_name, offering.sku, offering.metadata?.barcode,
    ...(offering.variants || []).filter((variant) => variant.is_active).flatMap((variant) => [variant.name, variant.sku, variant.barcode]),
  ].some((value) => normalize(value).includes(text));
}

export function findPosCodeMatches(offerings, code) {
  const text = normalize(code);
  if (!text) return [];
  return offerings.flatMap((offering) => {
    const variants = (offering.variants || []).filter((variant) =>
      variant.is_active && [variant.sku, variant.barcode].some((value) => value && normalize(value) === text),
    );
    if (variants.length) return variants.map((variant) => ({ offering, variantId: variant.public_id }));
    return [offering.sku, offering.metadata?.barcode].some((value) => value && normalize(value) === text)
      ? [{ offering, variantId: "" }]
      : [];
  });
}
