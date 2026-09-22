<template>
  <Sheet :open="cart.drawerOpen" @update:open="cart.drawerOpen = $event">
    <SheetContent class="flex w-full flex-col sm:max-w-md">
      <SheetHeader><SheetTitle>Your bag</SheetTitle><SheetDescription>{{ cart.itemCount }} {{ cart.itemCount === 1 ? 'item' : 'items' }} reserved when checkout is confirmed.</SheetDescription></SheetHeader>
      <div v-if="cart.loading" class="mt-6 space-y-4"><Skeleton v-for="index in 3" :key="index" class="h-24 w-full" /></div>
      <div v-else-if="cart.cart?.items?.length" class="mt-6 flex-1 divide-y overflow-y-auto">
        <article v-for="item in cart.cart.items" :key="item.public_id" class="py-5">
          <div class="flex justify-between gap-4"><div><h3 class="font-extrabold">{{ item.name }}</h3><p class="mt-1 text-xs text-muted-foreground">{{ item.metadata?.options?.map((option) => option.name).join(' · ') }}</p></div><strong>{{ money(Number(item.unit_price) * item.quantity) }}</strong></div>
          <div class="mt-3 flex items-center justify-between"><div class="flex items-center rounded-md border"><Button variant="ghost" size="icon" :disabled="item.quantity <= 1" :aria-label="`Decrease ${item.name} quantity`" @click="update(item, item.quantity - 1)"><Minus class="h-4 w-4" /></Button><span class="w-8 text-center text-sm font-bold tabular-nums">{{ item.quantity }}</span><Button variant="ghost" size="icon" :aria-label="`Increase ${item.name} quantity`" @click="update(item, item.quantity + 1)"><Plus class="h-4 w-4" /></Button></div><Button variant="ghost" class="text-destructive" @click="cart.remove(item.public_id)">Remove</Button></div>
        </article>
      </div>
      <StatePanel v-else class="mt-6" title="Your bag is empty" message="Products you add will stay with this business storefront." />
      <div v-if="cart.cart?.items?.length" class="border-t pt-5"><div class="flex items-center justify-between text-lg"><span class="font-semibold">Current total</span><strong>{{ money(cart.cart.totals.grand_total) }}</strong></div><p class="mt-2 text-xs leading-5 text-muted-foreground">Shipping and final availability are confirmed at checkout.</p><ButtonAnchor :href="`${base}/checkout`" class="mt-5 w-full">Checkout</ButtonAnchor><ButtonAnchor :href="`${base}/cart`" variant="outline" class="mt-2 w-full">View bag</ButtonAnchor></div>
    </SheetContent>
  </Sheet>
</template>

<script setup>
import { Minus, Plus } from 'lucide-vue-next'
const props = defineProps({ base: { type: String, required: true }, currency: { type: String, default: 'PHP' } })
const cart = useCartStore()
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0))
async function update(item, quantity) { await cart.updateItem(item.public_id, { quantity }) }
</script>
