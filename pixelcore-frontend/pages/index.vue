<template>
  <!-- DESIGN_CONTRACT: authored editorial landing page; the Living Pixel Core is the sole visual centerpiece and capability rows replace dashboard cards. -->
  <StorefrontPage v-if="customManifest" :manifest="customManifest" :offerings="customOfferings || []" base="" />
  <div v-else class="min-h-screen bg-background">
    <header class="border-b bg-background/95"><div class="mx-auto flex h-16 max-w-[90rem] items-center justify-between px-4 sm:px-6 lg:px-10"><NuxtLink to="/" aria-label="PixelCore home"><PixelCoreMark /></NuxtLink><nav class="flex items-center gap-1 sm:gap-2" aria-label="Account navigation"><ButtonLink variant="outline"  class="!border-transparent" to="/login">Sign in</ButtonLink><ButtonLink to="/register">Build your core</ButtonLink></nav></div></header>
    <main>
      <section class="border-b">
        <div class="mx-auto grid max-w-[90rem] lg:min-h-[calc(100vh-4rem)] lg:grid-cols-[minmax(0,.9fr)_minmax(34rem,1.1fr)]">
          <div class="flex flex-col justify-between px-4 py-14 sm:px-6 sm:py-20 lg:px-10 lg:py-14 xl:px-16 xl:py-20">
            <div class="max-w-[44rem] editorial-enter">
              <p class="mb-7 flex items-center gap-3 text-xs font-extrabold uppercase tracking-[.18em] text-muted-foreground"><span class="h-px w-10 bg-primary" /> Business infrastructure, made yours</p>
              <h1 class="display-face text-[clamp(3.1rem,6.2vw,6.7rem)] font-semibold leading-[.88] tracking-[-.045em]">Your business,<br><em class="font-medium text-primary">without the box.</em></h1>
              <p class="mt-8 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg sm:leading-8">PixelCore connects the pages customers see with the sales, schedules, people, and records your team runs behind them. Start from a useful preset. Change anything as the business changes.</p>
              <div class="mt-9 flex flex-wrap items-center gap-3"><ButtonLink to="/register" class="!min-h-12 !px-5">Create a workspace <ArrowUpRight class="h-4 w-4" aria-hidden="true" /></ButtonLink><ButtonAnchor variant="outline"  href="#system" class="!min-h-12 !px-5">See how it connects</ButtonAnchor></div>
            </div>
            <div class="mt-16 grid max-w-xl grid-cols-2 gap-x-6 gap-y-4 border-t pt-5 text-xs leading-5 text-muted-foreground sm:grid-cols-4 lg:mt-10">
              <p><strong class="block text-foreground">Philippine-first</strong> PHP and Manila defaults</p><p><strong class="block text-foreground">Business-owned</strong> Identity and payments</p><p><strong class="block text-foreground">Preset-aware</strong> Never preset-locked</p><p><strong class="block text-foreground">One catalog</strong> Products and services</p>
            </div>
          </div>
          <LivingPixelCore />
        </div>
      </section>
      <section id="system" class="mx-auto max-w-[90rem] px-4 py-20 sm:px-6 lg:px-10 lg:py-28 xl:px-16">
        <div class="grid gap-12 lg:grid-cols-[minmax(15rem,.55fr)_minmax(0,1.45fr)]">
          <div class="lg:sticky lg:top-24 lg:self-start"><p class="text-xs font-extrabold uppercase tracking-[.16em] text-primary">The connected system</p><h2 class="display-face mt-5 text-4xl font-semibold leading-tight tracking-[-.03em] sm:text-5xl">Four capabilities.<br>One business memory.</h2><p class="mt-5 max-w-md leading-7 text-muted-foreground">An order can change stock. A booking can reserve a room and update Calendar. A product can appear on your site, POS, QR catalog, and live display without being entered four times.</p></div>
          <ol class="border-t"><li v-for="(item, index) in capabilities" :key="item.title" class="group grid gap-4 border-b py-7 sm:grid-cols-[3rem_9rem_minmax(0,1fr)_auto] sm:items-start"><span class="font-mono text-xs text-muted-foreground">0{{ index + 1 }}</span><h3 class="text-lg font-extrabold">{{ item.title }}</h3><p class="max-w-2xl text-sm leading-6 text-muted-foreground">{{ item.copy }}</p><ArrowRight class="hidden h-5 w-5 text-primary transition-transform group-hover:translate-x-1 sm:block" aria-hidden="true" /></li></ol>
        </div>
      </section>
      <section class="border-y bg-secondary/45"><div class="mx-auto grid max-w-[90rem] gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_auto] lg:items-end lg:px-10 xl:px-16"><div><p class="text-xs font-extrabold uppercase tracking-[.16em] text-primary">Restaurant, retail, services, hybrid</p><h2 class="display-face mt-4 max-w-3xl text-4xl font-semibold leading-tight tracking-[-.025em]">Use the vocabulary that fits. Keep the capabilities that work.</h2><p class="mt-5 max-w-2xl leading-7 text-muted-foreground">Restaurant presets bring tables, reservations, Poster Menu, modifiers, nutrition, costing, attendance, and POS—without making every PixelCore business look like a restaurant.</p></div><ButtonLink to="/register" class="!min-h-12 !px-5">Start with PixelCore <ArrowRight class="h-4 w-4" aria-hidden="true" /></ButtonLink></div></section>
    </main>
  </div>
</template>

<script setup>
import { ArrowRight, ArrowUpRight } from 'lucide-vue-next'
definePageMeta({ layout: 'storefront' })
useHead({ title: 'PixelCore — Your business, without the box' })
const config = useRuntimeConfig(); const requestUrl = useRequestURL(); const hostname = requestUrl.hostname.toLowerCase()
const isCustomHost = !['localhost', '127.0.0.1', config.public.platformDomain].includes(hostname) && !hostname.endsWith(`.${config.public.platformDomain}`)
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const { data: customManifest } = useAsyncData('custom-domain-home', () => isCustomHost ? $fetch('public/site/resolve/', { baseURL, query: { host: hostname, path: '/' } }) : false)
const { data: customOfferings } = useAsyncData('custom-domain-catalog', () => customManifest.value ? $fetch(`public/${customManifest.value.identity.slug}/catalog/`, { baseURL }) : [])
const capabilities = [
  { title: 'Site', copy: 'Publish structured pages, QR catalogs, Poster Menu layouts, promotional screens, and verified domains from one media library.' },
  { title: 'Sell', copy: 'Use a shared catalog for storefront checkout and counter POS, with modifiers, promotions, customer displays, orders, and inventory-aware pricing.' },
  { title: 'Schedule', copy: 'Coordinate appointments, group sessions, tables, rooms, equipment, and staff through one collision-safe calendar and Google bridge.' },
  { title: 'Operate', copy: 'Keep workforce, attendance, purchasing, quotations, invoices, expenses, stock, and actual-result reports in the same business context.' },
]
</script>
