<template>
  <section class="border-b bg-secondary/30 px-4 py-10 sm:px-8 sm:py-14" aria-labelledby="marketplace-discovery-title">
    <div class="mx-auto max-w-4xl">
      <div class="mb-6 text-center">
        <component :is="primary ? 'h1' : 'h2'" id="marketplace-discovery-title" class="text-balance text-3xl font-semibold tracking-tight sm:text-5xl">
          {{ identity.branding?.storefront?.marketplace?.search_heading || "Find what you need. Discover what's next." }}
        </component>
        <p class="mt-3 text-sm leading-6 text-muted-foreground">
          {{ identity.branding?.storefront?.marketplace?.search_description || `Explore products, collections, and categories from ${identity.display_name}` }}
        </p>
      </div>
      <form class="rounded-2xl border-2 border-primary bg-background p-3 sm:p-5" role="search" @submit.prevent="search">
        <Label for="marketplace-home-search" class="sr-only">Search the store</Label>
        <Input
          id="marketplace-home-search"
          v-model.trim="query"
          type="search"
          placeholder="What are you looking for?"
          class="h-12 border-0 bg-transparent px-1 text-base shadow-none focus-visible:ring-0 sm:text-lg"
        />
        <div class="mt-3 flex flex-wrap items-center justify-between gap-3 border-t pt-3">
          <span class="flex items-center gap-2 text-xs text-muted-foreground">
            <Search class="h-4 w-4" aria-hidden="true" />
            Search by product name, brand, or keyword
          </span>
          <Button type="submit" class="ml-auto h-11 gap-2 rounded-full px-7">
            <Search class="h-4 w-4" aria-hidden="true" />
            Search
          </Button>
        </div>
      </form>
      <div v-if="categories.length" class="mt-5 flex flex-wrap items-center justify-center gap-2">
        <span class="mr-1 text-xs text-muted-foreground">Explore:</span>
        <a
          v-for="category in categories.slice(0, 5)"
          :key="category.slug"
          :href="`${base}/shop?category=${encodeURIComponent(category.slug)}`"
          class="rounded-full border bg-background px-4 py-2 text-xs font-medium transition-colors hover:border-primary hover:text-primary"
        >{{ category.name }}</a>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Search } from 'lucide-vue-next'

const props = defineProps({
  identity: { type: Object, required: true },
  primary: { type: Boolean, default: true },
  categories: { type: Array, default: () => [] },
  base: { type: String, required: true },
})
const query = ref('')
function search() {
  navigateTo(`${props.base}/shop${query.value ? '?search=' + encodeURIComponent(query.value) : ''}`)
}
</script>
