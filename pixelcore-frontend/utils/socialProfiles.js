const platformLabels = {
  facebook: 'Facebook',
  instagram: 'Instagram',
  linkedin: 'LinkedIn',
  tiktok: 'TikTok',
  x: 'X',
  youtube: 'YouTube',
}

export function socialPlatformLabel(platform) {
  return platformLabels[platform] || 'Social profile'
}

export function socialProfileHandle(profile) {
  try {
    const url = new URL(profile.url)
    const path = decodeURIComponent(url.pathname)
      .replace(/^\/+|\/+$/g, '')
      .replace(/^(@|in\/|company\/|channel\/|c\/|user\/)/, '')
    return path ? `@${path}` : url.hostname.replace(/^www\./, '')
  } catch {
    return socialPlatformLabel(profile.platform)
  }
}
