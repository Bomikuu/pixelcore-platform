<template>
  <section class="space-y-4 border-y py-5">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h3 class="font-semibold">Social profiles</h3>
        <p class="mt-1 max-w-md text-sm leading-5 text-muted-foreground">
          Add up to four professional profiles. They appear on the contact side.
        </p>
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        class="shrink-0 gap-2"
        :disabled="socialLinks.length >= 4"
        @click="addProfile"
      >
        <Plus class="h-4 w-4" aria-hidden="true" />
        Add profile
      </Button>
    </div>

    <div v-if="socialLinks.length" class="space-y-3">
      <div
        v-for="(profile, index) in socialLinks"
        :key="`${profile.platform}-${index}`"
        class="grid gap-3 rounded-xl bg-muted/55 p-3 sm:grid-cols-[9rem_minmax(0,1fr)_auto] sm:items-end"
      >
        <div class="space-y-2">
          <Label :for="`card-social-platform-${index}`">Platform</Label>
          <Select v-model="profile.platform">
            <SelectTrigger :id="`card-social-platform-${index}`">
              <SelectValue placeholder="Choose platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="platform in platforms"
                :key="platform.value"
                :value="platform.value"
              >
                {{ platform.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <Label :for="`card-social-url-${index}`">HTTPS profile URL</Label>
          <Input
            :id="`card-social-url-${index}`"
            v-model="profile.url"
            type="url"
            inputmode="url"
            autocomplete="url"
            placeholder="https://..."
          />
        </div>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          class="shrink-0"
          :aria-label="`Remove ${socialPlatformLabel(profile.platform)} profile`"
          @click="removeProfile(index)"
        >
          <Trash2 class="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>

    <div v-else class="flex items-start gap-3 rounded-xl bg-muted/55 px-4 py-5">
      <Share2 class="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
      <div>
        <p class="font-medium">No social profiles yet</p>
        <p class="mt-1 text-sm leading-5 text-muted-foreground">
          Add only profiles you want customers to use for professional contact.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Plus, Share2, Trash2 } from 'lucide-vue-next'
import { socialPlatformLabel } from '@/utils/socialProfiles'

const card = defineModel('card', {
  type: Object,
  required: true,
})

const socialLinks = computed(() =>
  Array.isArray(card.value.social_links) ? card.value.social_links : [],
)

const platforms = [
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'x', label: 'X' },
  { value: 'youtube', label: 'YouTube' },
]

function addProfile() {
  if (!Array.isArray(card.value.social_links)) card.value.social_links = []
  if (card.value.social_links.length >= 4) return
  card.value.social_links.push({ platform: 'instagram', url: '' })
}

function removeProfile(index) {
  card.value.social_links.splice(index, 1)
}
</script>
