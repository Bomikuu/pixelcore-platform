export const eventTypeOptions = [
  { value: 'wedding', label: 'Wedding' },
  { value: 'birthday', label: 'Birthday' },
  { value: 'general', label: 'General event' },
  { value: 'private_event', label: 'Private event' },
  { value: 'corporate', label: 'Corporate event' },
  { value: 'community', label: 'Community event' },
  { value: 'other', label: 'Other event' },
]

export const eventTemplates = [
  {
    value: 'wedding_editorial',
    group: 'wedding',
    label: 'Editorial noir',
    description: 'Monochrome photography, cinematic scale, and quiet transitions.',
    className: 'template-editorial',
    preset: {
      theme_background: '#080808',
      theme_text: '#F5F1E8',
      theme_accent: '#C8B99A',
      heading_font: 'Bodoni Moda',
      body_font: 'Manrope',
    },
  },
  {
    value: 'wedding_garden',
    group: 'wedding',
    label: 'Garden vow',
    description: 'An airy botanical invitation with framed vows, floral details, and intimate pacing.',
    className: 'template-garden',
    preset: {
      theme_background: '#162019',
      theme_text: '#F4EFE4',
      theme_accent: '#C7A77A',
      heading_font: 'Cormorant Garamond',
      body_font: 'Manrope',
    },
  },
  {
    value: 'wedding_modern',
    group: 'wedding',
    label: 'Modern ceremony',
    description: 'Architectural framing, sharp typography, and asymmetric composition.',
    className: 'template-modern',
    preset: {
      theme_background: '#111827',
      theme_text: '#F8FAFC',
      theme_accent: '#C6D4FF',
      heading_font: 'Italiana',
      body_font: 'Manrope',
    },
  },
  {
    value: 'birthday_color',
    group: 'birthday',
    label: 'Color story',
    description: 'Confident color fields, joyful scale, and an energetic welcome.',
    className: 'template-birthday-color',
    preset: {
      theme_background: '#461C3A',
      theme_text: '#FFF7ED',
      theme_accent: '#FFB45C',
      heading_font: 'Newsreader',
      body_font: 'Manrope',
    },
  },
  {
    value: 'birthday_after_dark',
    group: 'birthday',
    label: 'After dark',
    description: 'Nighttime contrast for dinner parties, dancing, and late celebrations.',
    className: 'template-after-dark',
    preset: {
      theme_background: '#120C24',
      theme_text: '#FAF5FF',
      theme_accent: '#D8B4FE',
      heading_font: 'Italiana',
      body_font: 'Manrope',
    },
  },
  {
    value: 'birthday_milestone',
    group: 'birthday',
    label: 'Milestone portrait',
    description: 'A composed, photo-led tribute for landmark birthdays.',
    className: 'template-milestone',
    preset: {
      theme_background: '#2A211B',
      theme_text: '#FAF7F2',
      theme_accent: '#D6B98C',
      heading_font: 'Bodoni Moda',
      body_font: 'Newsreader',
    },
  },
  {
    value: 'general_spotlight',
    group: 'general',
    label: 'Event spotlight',
    description: 'A bold opening for launches, galas, and headline occasions.',
    className: 'template-spotlight',
    preset: {
      theme_background: '#0E1B2B',
      theme_text: '#F8FAFC',
      theme_accent: '#67E8F9',
      heading_font: 'Italiana',
      body_font: 'Manrope',
    },
  },
  {
    value: 'general_studio',
    group: 'general',
    label: 'Studio programme',
    description: 'Clear sequencing and editorial restraint for formal programmes.',
    className: 'template-studio',
    preset: {
      theme_background: '#202020',
      theme_text: '#F5F5F4',
      theme_accent: '#D6D3D1',
      heading_font: 'Newsreader',
      body_font: 'Manrope',
    },
  },
  {
    value: 'general_community',
    group: 'general',
    label: 'Community canvas',
    description: 'Welcoming color and accessible rhythm for shared gatherings.',
    className: 'template-community',
    preset: {
      theme_background: '#18352E',
      theme_text: '#F0FDF4',
      theme_accent: '#86EFAC',
      heading_font: 'Cormorant Garamond',
      body_font: 'Manrope',
    },
  },
]

export function templateGroupForEventType(eventType) {
  if (eventType === 'wedding' || eventType === 'birthday') return eventType
  return 'general'
}

export function templatesForEventType(eventType) {
  const group = templateGroupForEventType(eventType)
  return eventTemplates.filter(template => template.group === group)
}

export function eventTemplate(value) {
  return eventTemplates.find(template => template.value === value) || eventTemplates[0]
}

export function eventTypeLabel(value) {
  return eventTypeOptions.find(option => option.value === value)?.label || 'Event'
}
