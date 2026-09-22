// Legacy assets and role-based media coexist. Gallery additions must not hide
// the original primary asset just because an ordered gallery now exists.
const imageKey = (item) => item.url
  ? item.url.replace(/^https?:\/\/[^/]+/, '')
  : item.asset_public_id || item.public_id

export function resolveProductCover(product) {
  const ordered = product?.ordered_media || []
  const cover = ordered.find((item) => item.role === 'cover' && !item.variant_public_id)
  if (cover) return cover
  const assigned = new Set(ordered.map(imageKey))
  return (product?.media || []).find((item) => !assigned.has(imageKey(item))) || null
}

export function productImages(product, activeVariantId = '') {
  const ordered = product?.ordered_media || []
  const cover = resolveProductCover(product)
  const photos = ordered.filter((item) => ['cover', 'gallery'].includes(item.role))
  const variant = activeVariantId ? photos.filter((item) => item.variant_public_id === activeVariantId) : []
  const gallery = photos.filter((item) => !item.variant_public_id && item.role === 'gallery')
  const source = [...variant, ...(cover ? [cover] : []), ...gallery]
  const seen = new Set()
  return source.filter((item) => {
    const key = imageKey(item)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}
