<template>
  <Tabs default-value="content" class="min-w-0">
    <TabsList class="grid h-auto w-full grid-cols-4">
      <TabsTrigger value="content" class="gap-2" aria-label="Card content">
        <Contact class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Content</span>
      </TabsTrigger>
      <TabsTrigger value="style" class="gap-2" aria-label="Card style">
        <Palette class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Style</span>
      </TabsTrigger>
      <TabsTrigger value="background" class="gap-2" aria-label="Card background">
        <ImageIcon class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Background</span>
      </TabsTrigger>
      <TabsTrigger value="sharing" class="gap-2" aria-label="Card sharing">
        <Share2 class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Sharing</span>
      </TabsTrigger>
    </TabsList>

    <TabsContent value="content" class="mt-7 space-y-7">
      <div class="grid gap-5 md:grid-cols-2">
        <div class="space-y-2">
          <Label for="card-name">Name</Label>
          <Input id="card-name" v-model="card.display_name" maxlength="160" required />
        </div>

        <div class="space-y-2">
          <Label for="card-title">Role or job title</Label>
          <Input
            id="card-title"
            v-model="card.job_title"
            maxlength="120"
            placeholder="Owner, designer, consultant…"
          />
        </div>

        <div class="space-y-2 md:col-span-2">
          <Label for="card-headline">Short introduction</Label>
          <Textarea
            id="card-headline"
            v-model="card.headline"
            class="min-h-28 resize-none"
            maxlength="220"
            placeholder="A concise line about your work or expertise."
          />
          <p class="text-right text-xs tabular-nums text-muted-foreground">
            {{ card.headline?.length || 0 }}/220
          </p>
        </div>

        <div class="space-y-2">
          <Label for="card-email">Email</Label>
          <Input
            id="card-email"
            v-model="card.email"
            type="email"
            autocomplete="email"
            maxlength="254"
          />
        </div>
        <div class="space-y-2">
          <Label for="card-phone">Phone</Label>
          <Input
            id="card-phone"
            v-model="card.phone"
            type="tel"
            autocomplete="tel"
            maxlength="32"
          />
        </div>
      </div>

      <BusinessCardSocialEditor v-model:card="card" />

      <Alert>
        <BadgeCheck class="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Auto-filled from your account</AlertTitle>
        <AlertDescription>
          This card started with your signed-in profile and business membership.
          Changes here affect only this card.
        </AlertDescription>
      </Alert>
    </TabsContent>

    <TabsContent value="style" class="mt-7 space-y-8">
      <div>
        <Label class="mb-3 block">Card composition</Label>
        <BusinessCardStylePicker v-model="card.style" />
      </div>

      <div class="space-y-2">
        <Label for="card-orientation">Orientation</Label>
        <Select v-model="card.orientation">
          <SelectTrigger id="card-orientation">
            <SelectValue placeholder="Choose orientation" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="landscape">Landscape · 3.5 × 2 in</SelectItem>
            <SelectItem value="portrait">Portrait · 2 × 3.5 in</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Separator />

      <BusinessCardDesignEditor
        v-model:card="card"
        :uploading="uploadingFont"
        @upload="$emit('upload-font', $event)"
      />

      <Alert>
        <Palette class="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Your business identity stays in control</AlertTitle>
        <AlertDescription>
          Every style uses the logo and validated colors from Appearance & branding.
        </AlertDescription>
      </Alert>
    </TabsContent>

    <TabsContent value="background" class="mt-6">
      <BusinessCardBackgroundEditor
        v-model:card="card"
        :assets="assets"
        :uploading="uploadingBackground"
        @upload="$emit('upload-background', $event)"
      />
    </TabsContent>

    <TabsContent value="sharing" class="mt-6 space-y-3">
      <VisibilityRow
        v-model="card.show_email"
        icon="mail"
        title="Show email"
        description="Display your card email on the contact side."
        :disabled="!card.email"
      />
      <VisibilityRow
        v-model="card.show_phone"
        icon="phone"
        title="Show phone"
        description="Display your phone number on the contact side."
        :disabled="!card.phone"
      />
      <VisibilityRow
        v-model="card.show_business_address"
        icon="map-pin"
        title="Show business address"
        description="Use the address saved in business identity settings."
        :disabled="!card.business_address"
      />
      <VisibilityRow
        v-model="card.show_social_links"
        icon="share"
        title="Show social profiles"
        description="Display the social profiles configured on this card."
        :disabled="!card.social_links?.length"
      />
      <VisibilityRow
        v-model="card.show_qr"
        icon="qr-code"
        title="Show QR code"
        description="Include a website or public-card QR on the contact side."
      />
      <Alert v-if="card.business_website_url">
        <QrCode class="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Website QR included</AlertTitle>
        <AlertDescription>
          The contact side automatically includes a QR for the website saved in
          business identity.
        </AlertDescription>
      </Alert>
      <Alert v-else>
        <QrCode class="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Public card QR fallback</AlertTitle>
        <AlertDescription>
          Once published, the QR opens this public card. Add a website if you want the
          QR to open your business site instead.
          <ButtonLink to="/settings/identity" size="sm" variant="outline" class="mt-4 w-fit gap-2">
            Open identity settings
            <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
          </ButtonLink>
        </AlertDescription>
      </Alert>

      <div class="mt-6 flex items-start justify-between gap-5 border-y py-5">
        <div>
          <Label for="card-published" class="leading-5">Publish public card</Label>
          <p class="mt-1 text-sm leading-5 text-muted-foreground">
            Anyone with the link can see the details you enabled above.
          </p>
        </div>
        <Switch id="card-published" v-model:checked="card.is_published" />
      </div>
    </TabsContent>
  </Tabs>
</template>

<script setup>
import {
  ArrowUpRight,
  BadgeCheck,
  Contact,
  Image as ImageIcon,
  Palette,
  QrCode,
  Share2,
} from 'lucide-vue-next'

defineProps({
  assets: { type: Array, default: () => [] },
  uploadingBackground: { type: Boolean, default: false },
  uploadingFont: { type: Boolean, default: false },
})

defineEmits(['upload-background', 'upload-font'])

const card = defineModel('card', {
  type: Object,
  required: true,
})
</script>
