<template>
  <form
    class="mx-auto mt-6 w-full rounded-2xl border border-white/20 bg-background/95 p-2 text-left text-foreground shadow-[0_18px_50px_rgba(0,0,0,0.2)] backdrop-blur sm:w-[42rem] sm:max-w-[calc(100vw-5rem)] sm:p-3"
    role="search"
    @submit.prevent="search"
  >
    <Label for="marketplace-carousel-search" class="sr-only">
      Search products, brands, and categories
    </Label>
    <div class="flex min-w-0 items-center gap-2">
      <Search class="ml-2 h-5 w-5 shrink-0 text-muted-foreground" aria-hidden="true" />
      <Input
        id="marketplace-carousel-search"
        v-model.trim="query"
        type="search"
        autocomplete="off"
        placeholder="What are you looking for?"
        class="h-12 min-w-0 flex-1 border-0 bg-transparent px-1 text-base shadow-none focus-visible:ring-0"
      />
      <Button type="submit" size="lg" class="shrink-0 gap-2 px-4 sm:px-6">
        <Search class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Search</span>
      </Button>
    </div>
    <div
      v-if="categories.length"
      class="flex items-center gap-2 overflow-x-auto border-t px-2 pt-2 text-xs"
      aria-label="Popular categories"
    >
      <span class="shrink-0 text-muted-foreground">Explore</span>
      <NuxtLink
        v-for="category in categories.slice(0, 4)"
        :key="category.slug"
        :to="`${base}/shop?category=${encodeURIComponent(category.slug)}`"
        class="shrink-0 rounded-full px-2 py-1 font-medium hover:bg-secondary hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {{ category.name }}
      </NuxtLink>
    </div>
  </form>
</template>

<script setup>
import { Search } from 'lucide-vue-next'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  base: { type: String, required: true },
})

const query = ref('')

function search() {
  const suffix = query.value ? `?search=${encodeURIComponent(query.value)}` : ''
  navigateTo(`${props.base}/shop${suffix}`)
}
</script>
