<template>
  <iframe
    :title="title"
    :srcdoc="document"
    sandbox=""
    referrerpolicy="no-referrer"
    class="block w-full border-0 bg-transparent"
    :class="heightClass"
  />
</template>

<script setup>
const props = defineProps({ html: { type: String, default: '' }, css: { type: String, default: '' }, title: { type: String, default: 'Custom business content' }, heightClass: { type: String, default: 'h-48' } })
const document = computed(() => {
  const css = String(props.css || '').replace(/<\/?style/gi, '')
  const markup = String(props.html || '')
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:"><style>:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;padding:16px;font:14px/1.55 Manrope,system-ui,sans-serif;color:#17312b;background:transparent}a{color:inherit;text-underline-offset:3px}${css}</style></head><body>${markup}</body></html>`
})
</script>
