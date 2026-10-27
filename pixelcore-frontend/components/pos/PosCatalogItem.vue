<template>
  <Button
    variant="ghost"
    type="button"
    :disabled="disabled"
    :aria-label="`${hasOptions ? 'Choose' : 'Add'} ${offering.name}${hasOptions ? '' : ' to order'}`"
    class="pos-catalog-item group h-auto min-h-0 items-stretch justify-start overflow-hidden bg-card p-0 text-left shadow-sm hover:bg-secondary/30"
    :class="view === 'list' ? 'flex-row gap-4 rounded-xl p-3' : 'flex-col gap-0 rounded-xl'"
    @click="$emit('add', offering)"
  >
    <div class="relative overflow-hidden" :class="view === 'list' ? 'w-24 shrink-0 rounded-lg' : 'w-full'">
      <ProductArtwork :name="offering.name" :type="offering.offering_type" :media="offering.media || []" />
      <Badge v-if="favorite && view === 'grid'" class="absolute left-2 top-2 gap-1 bg-foreground text-background hover:bg-foreground">
        <Star class="h-3 w-3" aria-hidden="true" /> Quick item
      </Badge>
    </div>
    <div class="flex min-w-0 flex-1 flex-col justify-center" :class="view === 'list' ? 'py-1' : 'p-3'">
      <p class="line-clamp-2 whitespace-normal text-sm font-bold leading-5">{{ offering.name }}</p>
      <p class="mt-1 truncate text-xs font-normal text-muted-foreground">
        {{ offering.category_name || typeLabel }}<span v-if="offering.sku"> · {{ offering.sku }}</span>
      </p>
      <div class="mt-3 flex items-end justify-between gap-2" :class="view === 'list' ? 'sm:mt-2' : ''">
        <span class="text-base font-extrabold tabular-nums text-primary">{{ price }}</span>
        <span class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-secondary text-primary group-hover:bg-primary group-hover:text-primary-foreground" aria-hidden="true">
          <Plus class="h-5 w-5" />
        </span>
      </div>
    </div>
  </Button>
</template>

<script setup>
import { Plus, Star } from "lucide-vue-next";

const props = defineProps({
  offering: { type: Object, required: true },
  price: { type: String, required: true },
  view: { type: String, default: "grid" },
  favorite: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
});
defineEmits(["add"]);
const hasOptions = computed(() => props.offering.variants?.some((variant) => variant.is_active) || props.offering.option_groups?.length);
const typeLabel = computed(() => ({ physical: "Product", service: "Service", digital: "Digital" }[props.offering.offering_type] || "Product"));
</script>

<style scoped>
.pos-catalog-item {
  white-space: normal;
}
</style>
