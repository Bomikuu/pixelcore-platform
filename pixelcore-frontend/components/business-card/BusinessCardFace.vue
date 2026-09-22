<template>
  <div
    class="business-card-face"
    :class="[
      `business-card-face--${card.style || 'signature'}`,
      `business-card-face--${side}`,
      usesImage ? 'business-card-face--with-image' : '',
    ]"
    :style="themeStyle"
  >
    <img
      v-if="usesImage"
      :src="card.background_image_url"
      alt=""
      class="business-card-background-image"
      :style="imageStyle"
    />
    <div
      v-if="usesImage && card.background_overlay !== 'none'"
      class="business-card-image-overlay"
      :style="overlayStyle"
      aria-hidden="true"
    />

    <div
      v-if="card.style === 'luxury'"
      class="business-card-luxury-frame"
      aria-hidden="true"
    >
      <span class="business-card-ornament business-card-ornament--top-left" />
      <span class="business-card-ornament business-card-ornament--top-right" />
      <span class="business-card-ornament business-card-ornament--bottom-left" />
      <span class="business-card-ornament business-card-ornament--bottom-right" />
    </div>

    <div v-if="side === 'front'" class="business-card-front-content">
      <div class="business-card-brand">
        <div class="business-card-logo">
          <img
            v-if="card.logo_url && !logoFailed"
            :src="card.logo_url"
            :alt="`${card.business_name} logo`"
            @error="logoFailed = true"
          />
          <span v-else aria-hidden="true">{{ businessInitial }}</span>
        </div>
        <div class="min-w-0">
          <p class="business-card-company">{{ card.business_name }}</p>
          <p v-if="card.business_tagline" class="business-card-tagline">
            {{ card.business_tagline }}
          </p>
        </div>
      </div>
    </div>

    <div v-else class="business-card-back-content">
      <div class="business-card-contact-heading">
        <div class="min-w-0">
          <p class="business-card-person">{{ card.display_name }}</p>
          <p v-if="card.job_title" class="business-card-role">
            {{ card.job_title }}
          </p>
        </div>
        <div class="business-card-mini-mark" aria-hidden="true">
          {{ businessInitial }}
        </div>
      </div>

      <p v-if="card.headline" class="business-card-headline">
        {{ card.headline }}
      </p>

      <div v-if="visibleSocialLinks.length" class="business-card-socials">
        <div
          v-for="profile in visibleSocialLinks"
          :key="profile.platform"
          class="business-card-social"
        >
          <SocialPlatformIcon
            :platform="profile.platform"
            class="business-card-social-icon"
          />
          <span>{{ socialProfileHandle(profile) }}</span>
        </div>
      </div>

      <div class="business-card-contact-layout">
        <div class="business-card-details">
          <p v-if="card.email" class="business-card-detail">
            <Mail class="h-[1em] w-[1em] shrink-0" aria-hidden="true" />
            <span>{{ card.email }}</span>
          </p>
          <p v-if="card.phone" class="business-card-detail">
            <Phone class="h-[1em] w-[1em] shrink-0" aria-hidden="true" />
            <span>{{ card.phone }}</span>
          </p>
          <p v-if="card.business_website_url" class="business-card-detail">
            <Globe2 class="h-[1em] w-[1em] shrink-0" aria-hidden="true" />
            <span>{{ websiteLabel }}</span>
          </p>
          <p
            v-if="card.business_address"
            class="business-card-detail business-card-address"
          >
            <MapPin class="h-[1em] w-[1em] shrink-0" aria-hidden="true" />
            <span>{{ card.business_address }}</span>
          </p>
        </div>

        <div v-if="qrDataUrl && card.show_qr !== false" class="business-card-qr">
          <img
            :src="qrDataUrl"
            :alt="`QR code for ${card.business_name}`"
          />
          <span>{{ qrLabel }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Globe2, Mail, MapPin, Phone } from 'lucide-vue-next'
import SocialPlatformIcon from '@/components/site/SocialPlatformIcon.vue'
import { socialProfileHandle } from '@/utils/socialProfiles'

const props = defineProps({
  card: { type: Object, required: true },
  side: { type: String, default: 'front' },
  qrDataUrl: { type: String, default: '' },
  qrLabel: { type: String, default: 'Visit website' },
})

const logoFailed = ref(false)
const visibleSocialLinks = computed(() =>
  props.card.show_social_links === false || !Array.isArray(props.card.social_links)
    ? []
    : props.card.social_links.slice(0, 4),
)
const businessInitial = computed(() =>
  String(props.card.business_name || 'B').charAt(0).toUpperCase(),
)
const websiteLabel = computed(() => {
  try {
    return new URL(props.card.business_website_url).hostname.replace(/^www\./, '')
  } catch {
    return props.card.business_website_url
  }
})
const usesImage = computed(() => {
  const target = props.card.background_apply_to || 'front'
  return Boolean(
    props.card.background_type === 'image' &&
      props.card.background_image_url &&
      (target === 'both' || target === props.side),
  )
})
const imageStyle = computed(() => ({
  objectFit: props.card.background_image_fit || 'cover',
  objectPosition: props.card.background_image_position || 'center',
}))
const overlayStyle = computed(() => {
  const opacity = {
    low: 0.24,
    medium: 0.44,
    high: 0.64,
  }[props.card.background_overlay_strength || 'medium']
  const backgrounds = {
    light: `rgb(255 255 255 / ${opacity})`,
    dark: `rgb(5 15 14 / ${opacity})`,
    brand: `color-mix(in srgb, var(--card-primary) ${opacity * 100}%, transparent)`,
  }
  return { background: backgrounds[props.card.background_overlay] || 'transparent' }
})

const fontFamilies = {
  manrope: 'Manrope, ui-sans-serif, sans-serif',
  newsreader: 'Newsreader, Georgia, serif',
  playfair: '"Playfair Display", Georgia, serif',
  cormorant: '"Cormorant Garamond", Georgia, serif',
  montserrat: 'Montserrat, ui-sans-serif, sans-serif',
  jakarta: '"Plus Jakarta Sans", ui-sans-serif, sans-serif',
  great_vibes: '"Great Vibes", cursive',
  allura: 'Allura, cursive',
  parisienne: 'Parisienne, cursive',
  alex_brush: '"Alex Brush", cursive',
  lobster: 'Lobster, cursive',
  playball: 'Playball, cursive',
}

function resolveFont(font, fallback) {
  if (font === 'custom' && props.card._custom_font_family) {
    return `"${props.card._custom_font_family}", ${fallback}`
  }
  return fontFamilies[font] || fallback
}

const themeStyle = computed(() => {
  const theme = props.card.theme || {}
  const styleFont = {
    modern: 'Manrope, ui-sans-serif, sans-serif',
    editorial: 'Newsreader, Georgia, serif',
    geometric: 'Montserrat, ui-sans-serif, sans-serif',
    warm: '"Plus Jakarta Sans", ui-sans-serif, sans-serif',
  }[props.card.font_style || 'modern']
  const isLuxury = props.card.style === 'luxury'
  const customColors = props.card.color_mode === 'custom'
  const customTypography = props.card.typography_mode === 'custom'

  const background = customColors
    ? props.card.background_color || '#0B0B0D'
    : isLuxury
      ? '#0B0B0D'
      : theme.background_color || '#FAF9F5'
  const text = customColors
    ? props.card.text_color || '#F8F1E1'
    : isLuxury
      ? '#F8F1E1'
      : theme.text_color || '#17312B'
  const accent = customColors
    ? props.card.accent_color || '#C8A96B'
    : isLuxury
      ? '#C8A96B'
      : theme.accent_color || '#D8922B'
  const border = customColors
    ? props.card.border_color || accent
    : isLuxury
      ? '#BFA36A'
      : accent
  const ornament = customColors
    ? props.card.ornament_color || accent
    : isLuxury
      ? '#C8A96B'
      : accent
  const foreground = customColors
    ? text
    : isLuxury
      ? '#F8F1E1'
      : props.card.style === 'studio'
        ? theme.text_color || '#17312B'
        : '#FFFFFF'

  const headingFont = customTypography
    ? resolveFont(props.card.heading_font, styleFont)
    : isLuxury
      ? '"Cormorant Garamond", Georgia, serif'
      : styleFont
  const bodyFont = customTypography
    ? resolveFont(props.card.body_font, styleFont)
    : isLuxury
      ? 'Manrope, ui-sans-serif, sans-serif'
      : styleFont
  const accentFont = customTypography
    ? resolveFont(props.card.accent_font, headingFont)
    : isLuxury
      ? '"Great Vibes", cursive'
      : styleFont

  return {
    '--card-primary': customColors
      ? props.card.style === 'studio' ? accent : background
      : theme.primary_color || '#165B4C',
    '--card-secondary': customColors
      ? background
      : theme.secondary_color || '#17362F',
    '--card-accent': accent,
    '--card-paper': background,
    '--card-ink': text,
    '--card-border': border,
    '--card-ornament': ornament,
    '--card-foreground': foreground,
    '--card-on-accent': customColors ? text : '#FFFFFF',
    '--card-luxury-background': background,
    '--card-luxury-text': text,
    '--card-luxury-accent': accent,
    '--card-luxury-border': border,
    '--card-luxury-ornament': ornament,
    '--card-heading-font': headingFont,
    '--card-body-font': bodyFont,
    '--card-accent-font': accentFont,
    '--card-font': bodyFont,
  }
})

watch(
  () => props.card.logo_url,
  () => {
    logoFailed.value = false
  },
)
</script>

<style src="./BusinessCardFace.css" scoped></style>
