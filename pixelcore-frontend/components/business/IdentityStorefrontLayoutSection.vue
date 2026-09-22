<template>
  <div class="space-y-8">
    <header>
      <h2 class="text-xl font-extrabold">Shop layout</h2>
      <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
        Choose how customers browse. Products, inventory, checkout, identity,
        and CMS content stay connected when the layout changes.
      </p>
    </header>

    <div class="grid gap-4 lg:grid-cols-2">
      <Button
        v-for="layout in layouts"
        :key="layout.id"
        type="button"
        variant="outline"
        class="h-auto min-h-48 items-stretch justify-start whitespace-normal p-0 text-left"
        :class="activeLayout === layout.id ? 'border-primary ring-2 ring-primary/20' : ''"
        :aria-pressed="activeLayout === layout.id"
        @click="selectLayout(layout.id)"
      >
        <span class="flex w-full flex-col p-5">
          <span class="flex items-start justify-between gap-4">
            <span class="grid h-10 w-10 place-items-center rounded-lg bg-secondary text-primary">
              <component :is="layout.icon" class="h-5 w-5" aria-hidden="true" />
            </span>
            <Badge v-if="activeLayout === layout.id">Selected</Badge>
          </span>
          <strong class="mt-5 text-lg">{{ layout.name }}</strong>
          <span class="mt-2 text-sm font-normal leading-6 text-muted-foreground">
            {{ layout.description }}
          </span>
          <span class="mt-auto pt-5 text-xs font-bold text-primary">
            {{ layout.structure }}
          </span>
        </span>
      </Button>
    </div>

    <Alert>
      <Blocks class="h-4 w-4" aria-hidden="true" />
      <AlertTitle>One catalog, two customer experiences</AlertTitle>
      <AlertDescription>
        Brand storefront is suited to focused collections and visual launches.
        Marketplace is suited to larger catalogs, frequent search, deals, and
        comparison shopping.
      </AlertDescription>
    </Alert>

    <section v-if="activeLayout === 'brand'" class="border-t pt-8">
      <IdentityStorefrontModeSection :form="form" />
    </section>

    <section v-else class="border-t pt-8" aria-labelledby="marketplace-style-heading">
      <div class="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 id="marketplace-style-heading" class="font-extrabold">
            Marketplace styling
          </h3>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Use your current colors and fonts, or apply a compact retail preset
            designed for search, category navigation, and product-dense pages.
          </p>
        </div>
        <Button type="button" variant="outline" class="shrink-0 gap-2" @click="applyMarketplacePreset">
          <WandSparkles class="h-4 w-4" aria-hidden="true" />
          Apply marketplace styling
        </Button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Blocks, LayoutGrid, PanelsTopLeft, WandSparkles } from "lucide-vue-next";
import { toast } from "@/components/ui/toast";
import IdentityStorefrontModeSection from "./IdentityStorefrontModeSection.vue";

const props = defineProps({
  form: {
    type: Object,
    required: true,
  },
});

const storefront = computed(() => props.form.branding.storefront);
const activeLayout = computed(() => storefront.value.layout || "brand");

const layouts = [
  {
    id: "brand",
    name: "Brand storefront",
    icon: PanelsTopLeft,
    description:
      "An image-led shop for brand stories, collection launches, and focused product discovery. Includes the existing Default and Luxury modes.",
    structure: "Nike and luxury retail style",
  },
  {
    id: "marketplace",
    name: "Marketplace",
    icon: LayoutGrid,
    description:
      "A search-first shop for broad catalogs, category browsing, deal visibility, comparison, and fast repeat purchasing.",
    structure: "Amazon, Alibaba, and Lazada style",
  },
];

function selectLayout(layout) {
  storefront.value.layout = layout;
}

function applyMarketplacePreset() {
  Object.assign(props.form.branding, {
    primary_color: "#0F766E",
    secondary_color: "#E7F3F1",
    accent_color: "#F59E0B",
    background_color: "#F5F6F6",
    text_color: "#17211F",
    muted_text_color: "#66736F",
    link_color: "#0F766E",
  });
  Object.assign(props.form.branding.typography, {
    primary_font: "Inter",
    heading_font: "Inter",
    body_weight: 400,
    heading_weight: 700,
    base_font_size: "16px",
  });
  Object.assign(props.form.branding.style, {
    button_radius: "medium",
    card_radius: "medium",
    input_radius: "medium",
    modal_radius: "large",
    border_width: "thin",
    shadow_intensity: "subtle",
    content_width: "full",
  });
  Object.assign(storefront.value.background, {
    type: "color",
    color: "#F5F6F6",
  });
  toast({
    title: "Marketplace styling applied",
    description: "Review the preview, then save identity to publish the layout.",
  });
}
</script>
