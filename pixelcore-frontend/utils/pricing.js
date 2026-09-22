export function discountPercentage(price, compareAtPrice) {
  const current = Number(price)
  const original = Number(compareAtPrice)
  if (!Number.isFinite(current) || !Number.isFinite(original) || original <= 0 || current >= original) return 0
  return Math.round(((original - current) / original) * 100)
}

export function discountLabel(price, compareAtPrice) {
  const percentage = discountPercentage(price, compareAtPrice)
  return percentage ? `${percentage}% off` : ''
}
