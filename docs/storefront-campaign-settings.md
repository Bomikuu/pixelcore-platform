# Storefront campaigns

In Settings → Appearance & branding:

- **Hero & background → Marketplace home hero:** choose Campaign carousel, Integrated carousel, or Search-led. The integrated option places product search and category shortcuts inside the active campaign instead of creating a second hero below it. Customize width, height, autoplay, interval, search copy, and up to five ordered campaign slides. Slides reuse the existing media upload/editor and support images, video, approved GLB models, and controlled particles.
- If no custom slides are configured, the Marketplace home uses the configured global hero, CMS custom slides, or published product imagery. The discovery panel retains its compact hero only in Search-led mode to avoid duplicating the main carousel.
- **Popup:** enable the campaign; choose Image + message, Split layout, or Image-only poster; choose size, delay, frequency, and home-page-only visibility. Poster artwork is displayed without cropping and can link to a destination. Existing custom HTML/CSS stays sandboxed.
- **Preview popup** renders the actual popup with unsaved settings. It bypasses timing and frequency, disables destination navigation, and does not record a visitor impression. Carousel previews similarly disable action navigation.
- Save identity to publish. Popup frequency supports session, rolling 24-hour, or every eligible page visit. A changed campaign gets a new storage key so an old dismissal does not suppress it. No popup is enabled automatically.

All configuration remains in the existing business identity JSON. Asset references are tenant-owned, validated, and included in the public branding asset map. No migration or dependency rebuild is required. DineEase remains untouched.
