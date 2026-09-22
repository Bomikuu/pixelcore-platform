<template>
  <section id="product-reviews" class="scroll-mt-40 border-t py-8" aria-labelledby="reviews-heading">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h2 id="reviews-heading" class="text-xl font-semibold">Customer reviews</h2>
        <p class="mt-2 text-sm text-muted-foreground">Experiences from customers who purchased this product.</p>
      </div>
      <Button variant="outline" class="gap-2" @click="openEditor">
        <PenLine class="h-4 w-4" aria-hidden="true" />Write a review
      </Button>
    </div>

    <div class="mt-6 grid gap-8 lg:grid-cols-[18rem_minmax(0,1fr)] lg:gap-12">
      <div>
        <div class="flex items-baseline gap-2">
          <strong class="text-5xl font-semibold tracking-tight tabular-nums">{{ summary.count ? Number(summary.average).toFixed(1) : '—' }}</strong>
          <span class="text-sm text-muted-foreground">out of 5</span>
        </div>
        <p class="mt-2 text-sm text-muted-foreground">{{ summary.count }} {{ summary.count === 1 ? 'review' : 'reviews' }}</p>
        <div class="mt-5 space-y-1" aria-label="Filter reviews by rating">
          <Button
            v-for="row in summary.distribution || emptyDistribution"
            :key="row.rating"
            variant="ghost"
            class="h-10 w-full gap-3 px-2 text-sm"
            :class="rating === String(row.rating) ? 'bg-secondary' : ''"
            :aria-label="`${row.rating} stars, ${row.count} reviews`"
            :aria-pressed="rating === String(row.rating)"
            @click="rating = rating === String(row.rating) ? 'all' : String(row.rating)"
          >
            <span class="flex w-7 items-center gap-1">{{ row.rating }}<Star class="h-3 w-3" aria-hidden="true" /></span>
            <span class="h-2 flex-1 overflow-hidden rounded-full bg-secondary" aria-hidden="true">
              <span class="block h-full rounded-full bg-primary" :style="{ width: `${summary.count ? row.count / summary.count * 100 : 0}%` }" />
            </span>
            <span class="w-6 text-right tabular-nums text-muted-foreground">{{ row.count }}</span>
          </Button>
        </div>
        <Button v-if="rating !== 'all'" variant="link" class="mt-2 px-0" @click="rating = 'all'">Clear rating filter</Button>
      </div>

      <div class="min-w-0" :aria-busy="status === 'pending'">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3 border-b pb-4">
          <p class="text-sm font-medium">{{ rating === 'all' ? 'All ratings' : `${rating}-star reviews` }}</p>
          <div class="flex items-center gap-2">
            <Label for="review-sort" class="text-xs text-muted-foreground">Sort by</Label>
            <Select v-model="ordering">
              <SelectTrigger id="review-sort" class="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Most recent</SelectItem>
                <SelectItem value="highest">Highest rating</SelectItem>
                <SelectItem value="lowest">Lowest rating</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div v-if="status === 'pending'" class="space-y-4 py-4" role="status">
          <span class="sr-only">Loading reviews</span>
          <Skeleton class="h-5 w-32" /><Skeleton class="h-4 w-3/4" /><Skeleton class="h-4 w-1/2" />
        </div>
        <Alert v-else-if="error" variant="destructive">
          <AlertTitle>Reviews could not be loaded</AlertTitle>
          <AlertDescription><Button variant="link" class="h-auto px-0 text-inherit" @click="refresh">Try again</Button></AlertDescription>
        </Alert>
        <div v-else-if="!data?.results?.length" class="py-10">
          <MessageSquare class="mb-4 h-7 w-7 text-muted-foreground" aria-hidden="true" />
          <h3 class="font-semibold">{{ summary.count ? 'No reviews with this rating' : 'Be the first to share your experience' }}</h3>
          <p class="mt-2 max-w-lg text-sm leading-6 text-muted-foreground">{{ summary.count ? 'Choose another rating to read more customer experiences.' : 'After your purchase, tell other shoppers about the quality, fit, and everyday details.' }}</p>
        </div>
        <div v-else class="divide-y">
          <article v-for="review in data.results" :key="review.public_id" class="py-6 first:pt-2">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <span class="grid h-9 w-9 place-items-center rounded-full bg-secondary text-sm font-semibold" aria-hidden="true">{{ review.author_name.slice(0, 1).toUpperCase() }}</span>
                <div>
                  <p class="text-sm font-semibold">{{ review.author_name }}</p>
                  <p v-if="review.verified_purchase" class="mt-1 flex items-center gap-1 text-xs text-primary"><BadgeCheck class="h-3.5 w-3.5" aria-hidden="true" />Verified purchase</p>
                </div>
              </div>
              <time :datetime="review.created_at" class="text-xs text-muted-foreground">{{ formatDate(review.created_at) }}</time>
            </div>
            <div class="mt-4 flex gap-0.5 text-primary" :aria-label="`${review.rating} out of 5 stars`">
              <Star v-for="star in 5" :key="star" class="h-4 w-4" :class="star <= review.rating ? 'fill-current' : ''" aria-hidden="true" />
            </div>
            <h3 class="mt-3 break-words font-semibold">{{ review.title }}</h3>
            <p class="mt-2 max-w-prose whitespace-pre-line break-words text-sm leading-7 text-muted-foreground">{{ review.body }}</p>
          </article>
        </div>
        <nav v-if="data?.count > 5" class="mt-4 flex items-center justify-between gap-3 border-t pt-4" aria-label="Review pagination">
          <p class="text-xs text-muted-foreground">Page {{ page }} of {{ Math.ceil(data.count / 5) }}</p>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" :disabled="page <= 1 || status === 'pending'" @click="page--">Previous</Button>
            <Button variant="outline" size="sm" :disabled="!data.next || status === 'pending'" @click="page++">Next</Button>
          </div>
        </nav>
      </div>
    </div>

    <Dialog v-model:open="editorOpen">
      <DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{{ mine?.review ? 'Edit your review' : 'Review this product' }}</DialogTitle>
          <DialogDescription>{{ productName }}</DialogDescription>
        </DialogHeader>
        <p v-if="loadingAccount" class="flex items-center gap-2 py-8 text-sm" role="status"><LoaderCircle class="h-4 w-4 animate-spin" aria-hidden="true" />Checking your purchase…</p>
        <div v-else-if="!auth.isAuthenticated" class="space-y-4 py-4">
          <p class="text-sm leading-6 text-muted-foreground">Sign in to the account linked to your purchase to write a review. Your first name and review will be public; your email will not.</p>
          <ButtonLink :to="`/login?next=${encodeURIComponent(route.fullPath.split('#')[0] + '#product-reviews')}`">Sign in to review</ButtonLink>
        </div>
        <Alert v-else-if="accountError" variant="destructive"><AlertTitle>Unable to check your account</AlertTitle><AlertDescription>{{ accountError }}<Button variant="link" @click="openEditor">Try again</Button></AlertDescription></Alert>
        <div v-else-if="!mine?.can_review && !mine?.review" class="py-4">
          <h3 class="font-semibold">A linked purchase is required</h3>
          <p class="mt-2 text-sm leading-6 text-muted-foreground">Only customers with a paid purchase of this product linked to their account can review it. If you checked out as a guest, visit your store account to link your orders first.</p>
          <ButtonLink :to="accountPath" variant="outline" class="mt-4">View my store account</ButtonLink>
        </div>
        <form v-else class="space-y-5" @submit.prevent="saveReview">
          <Alert v-if="mine?.is_visible === false"><AlertTitle>Review hidden</AlertTitle><AlertDescription>This review is not public. Editing it will not override moderation.</AlertDescription></Alert>
          <fieldset :disabled="saving || !mine?.can_review">
            <legend class="text-sm font-medium">Your rating</legend>
            <div class="mt-2 flex gap-1">
              <Button v-for="star in 5" :key="star" type="button" variant="ghost" size="icon" :aria-label="`${star} out of 5 stars`" :aria-pressed="form.rating === star" @click="form.rating = star">
                <Star class="h-6 w-6 text-primary" :class="star <= form.rating ? 'fill-current' : ''" aria-hidden="true" />
              </Button>
            </div>
            <Label for="review-title" class="mt-5 block">Review title</Label>
            <Input id="review-title" v-model="form.title" required maxlength="120" class="mt-2" placeholder="What stood out?" />
            <Label for="review-body" class="mt-5 block">Your experience</Label>
            <Textarea id="review-body" v-model="form.body" required maxlength="3000" :rows="5" class="mt-2" placeholder="Share the details you would want to know before buying." />
            <p class="mt-2 text-xs text-muted-foreground">{{ form.body.length }}/3,000 · Your first name and review will be public. Do not include contact or order details.</p>
          </fieldset>
          <p v-if="formError" class="text-sm text-destructive" role="alert">{{ formError }}</p>
          <DialogFooter class="gap-2">
            <Button v-if="mine?.review" type="button" variant="ghost" class="mr-auto gap-2 text-destructive" :disabled="saving" @click="deleteOpen = true"><Trash2 class="h-4 w-4" aria-hidden="true" />Delete</Button>
            <Button type="button" variant="outline" :disabled="saving" @click="editorOpen = false">Cancel</Button>
            <Button type="submit" class="gap-2" :disabled="saving || !mine?.can_review || !form.rating || !form.title.trim() || !form.body.trim()"><LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />{{ saving ? 'Saving…' : 'Save review' }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
    <Dialog v-model:open="deleteOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete your review?</DialogTitle>
          <DialogDescription>Your rating and written review will be removed. This cannot be undone.</DialogDescription>
        </DialogHeader>
        <p v-if="formError" class="text-sm text-destructive" role="alert">{{ formError }}</p>
        <DialogFooter>
          <Button variant="outline" :disabled="saving" @click="deleteOpen = false">Keep review</Button>
          <Button variant="destructive" :disabled="saving" @click="deleteReview">{{ saving ? 'Deleting…' : 'Delete review' }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </section>
</template>

<script setup>
import { BadgeCheck, LoaderCircle, MessageSquare, PenLine, Star, Trash2 } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'

const props = defineProps({
  slug: { type: String, required: true },
  productSlug: { type: String, required: true },
  productName: { type: String, required: true },
  initialSummary: { type: Object, default: () => ({ count: 0, average: null }) },
})
const emit = defineEmits(['summary'])
const config = useRuntimeConfig()
const route = useRoute()
const auth = useAuthStore()
const { apiFetch } = useApiClient()
const endpoint = computed(() => `public/${props.slug}/storefront/products/${props.productSlug}/reviews/`)
const accountPath = computed(() => route.path.startsWith('/site/') ? `/site/${props.slug}/account` : '/account')
const page = ref(1)
const rating = ref('all')
const ordering = ref('newest')
const emptyDistribution = [5, 4, 3, 2, 1].map((value) => ({ rating: value, count: 0 }))
const { data, status, error, refresh } = await useAsyncData(
  `reviews-${props.slug}-${props.productSlug}`,
  () => $fetch(endpoint.value, {
    baseURL: import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl,
    query: { page: page.value, rating: rating.value === 'all' ? undefined : rating.value, ordering: ordering.value },
  }),
  { watch: [page, rating, ordering] },
)
const summary = computed(() => data.value?.summary || props.initialSummary || { count: 0, average: null })
watch([rating, ordering], () => { page.value = 1 })
watch(summary, (value) => emit('summary', value), { immediate: true })

const editorOpen = ref(false)
const deleteOpen = ref(false)
const loadingAccount = ref(false)
const accountError = ref('')
const mine = ref(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ rating: 0, title: '', body: '' })

function formatDate(value) {
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium' }).format(new Date(value))
}

async function openEditor() {
  editorOpen.value = true
  loadingAccount.value = true
  accountError.value = ''
  formError.value = ''
  try {
    await auth.restoreSession()
    if (!auth.isAuthenticated) return
    mine.value = await apiFetch(`${endpoint.value}mine/`)
    Object.assign(form, { rating: mine.value.review?.rating || 0, title: mine.value.review?.title || '', body: mine.value.review?.body || '' })
  } catch (error) {
    accountError.value = error?.data?.error?.message || 'Please try again.'
  } finally {
    loadingAccount.value = false
  }
}

async function saveReview() {
  if (saving.value) return
  saving.value = true
  formError.value = ''
  try {
    await apiFetch(`${endpoint.value}mine/`, { method: 'PUT', body: { ...form } })
    editorOpen.value = false
    toast({ title: 'Review saved', description: mine.value?.is_visible === false ? 'Your changes are saved. The review remains hidden.' : 'Thank you for sharing your experience.' })
    await refresh()
  } catch (error) {
    formError.value = error?.data?.error?.message || 'Your review could not be saved. Please try again.'
  } finally {
    saving.value = false
  }
}

async function deleteReview() {
  saving.value = true
  formError.value = ''
  try {
    await apiFetch(`${endpoint.value}mine/`, { method: 'DELETE' })
    deleteOpen.value = false
    editorOpen.value = false
    toast({ title: 'Review deleted' })
    page.value = 1
    await refresh()
  } catch (error) {
    formError.value = error?.data?.error?.message || 'Your review could not be deleted. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>
