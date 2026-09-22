<template>
  <section class="workspace-page space-y-7">
    <PageHeader
      title="Business card"
      description="Create a print-ready card and one public contact link from your business identity."
    >
      <template #actions>
        <Badge
          :variant="card?.is_published ? 'default' : 'secondary'"
          class="h-10 min-w-28 justify-center gap-2 rounded-md px-4 text-sm font-semibold shadow-sm"
        >
          <Globe2 v-if="card?.is_published" class="h-4 w-4" aria-hidden="true" />
          <FilePenLine v-else class="h-4 w-4" aria-hidden="true" />
          {{ card?.is_published ? 'Published' : 'Draft' }}
        </Badge>
        <Button
          type="button"
          variant="outline"
          class="gap-2"
          :disabled="!publicPath"
          @click="openPublicPreview"
        >
          <Eye class="h-4 w-4" aria-hidden="true" />
          Preview
        </Button>
        <Button
          type="button"
          variant="outline"
          class="gap-2"
          :disabled="!publicPath"
          @click="copyPublicLink"
        >
          <Copy class="h-4 w-4" aria-hidden="true" />
          Copy link
        </Button>
        <Button
          type="button"
          variant="outline"
          class="gap-2"
          :disabled="!card"
          @click="printCard"
        >
          <Printer class="h-4 w-4" aria-hidden="true" />
          Print
        </Button>
        <Button
          type="button"
          class="gap-2"
          :disabled="saving || !canSave"
          @click="saveCard"
        >
          <LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
          <Save v-else class="h-4 w-4" aria-hidden="true" />
          {{ saving ? 'Saving' : 'Save card' }}
        </Button>
      </template>
    </PageHeader>

    <StatePanel
      v-if="loading"
      kind="loading"
      title="Preparing your card"
      message="Combining your member profile with the active business identity."
    />
    <StatePanel
      v-else-if="error"
      kind="error"
      title="Business card unavailable"
      :message="error"
    >
      <Button type="button" variant="outline" @click="loadCard">Try again</Button>
    </StatePanel>

    <div
      v-else-if="card"
      class="grid gap-8 xl:grid-cols-[minmax(34rem,0.95fr)_minmax(0,1.15fr)] xl:items-start 2xl:grid-cols-[minmax(38rem,0.95fr)_minmax(0,1.2fr)]"
    >
      <Card class="min-w-0 overflow-hidden">
        <CardHeader class="border-b bg-muted/20 px-6 py-6 sm:px-8">
          <CardTitle class="text-xl">Build your card</CardTitle>
          <CardDescription>
            Edit content, art direction, background, and sharing from one workspace.
          </CardDescription>
        </CardHeader>
        <CardContent class="px-6 py-7 sm:px-8 sm:py-8">
          <BusinessCardEditor
            v-model:card="card"
            :assets="assets"
            :uploading-background="uploadingBackground"
            :uploading-font="uploadingFont"
            @upload-background="uploadBackground"
            @upload-font="uploadFont"
          />
        </CardContent>
      </Card>

      <aside
        class="order-first min-w-0 xl:order-last xl:sticky xl:top-20"
        aria-label="Business card preview"
      >
        <div
          class="overflow-hidden rounded-2xl bg-foreground px-5 py-8 sm:px-9 sm:py-10 xl:min-h-[36rem] xl:px-10 xl:py-12"
        >
          <div
            class="mx-auto mb-9 flex max-w-[46rem] items-center justify-between gap-4 text-background"
          >
            <div>
              <h2 class="text-lg font-semibold">Live preview</h2>
              <p class="mt-1 max-w-md text-sm leading-5 text-background/65">
                Select the card to move between the brand and contact sides.
              </p>
            </div>
            <Badge variant="outline" class="border-background/25 text-background">
              {{ card.orientation }}
            </Badge>
          </div>
          <div class="business-card-preview-print xl:py-3">
            <BusinessCardCanvas
              :card="card"
              :qr-fallback-url="publicUrl"
              printable
            />
          </div>
        </div>

        <div
          class="mt-4 flex flex-col gap-3 border-y py-4 text-sm sm:flex-row sm:items-center sm:justify-between"
        >
          <div class="flex items-start gap-2 text-muted-foreground">
            <QrCode class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
            <span>
              {{ card.business_website_url
                ? 'The QR opens the website saved in Appearance & branding.'
                : publicUrl
                  ? 'No website is saved, so the QR opens this public card.'
                  : 'Publish this card or add a business website to enable the QR.' }}
            </span>
          </div>
          <ButtonAnchor
            v-if="publicPath"
            :href="publicPath"
            target="_blank"
            rel="noopener"
            variant="ghost"
            size="sm"
            class="shrink-0 gap-2"
          >
            Open public card
            <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
          </ButtonAnchor>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup>
import {
  ArrowUpRight,
  Copy,
  Eye,
  FilePenLine,
  Globe2,
  LoaderCircle,
  Printer,
  QrCode,
  Save,
} from 'lucide-vue-next'

const {
  assets,
  canSave,
  card,
  copyPublicLink,
  error,
  loadCard,
  loading,
  openPublicPreview,
  printCard,
  publicPath,
  publicUrl,
  saveCard,
  saving,
  uploadBackground,
  uploadFont,
  uploadingBackground,
  uploadingFont,
} = useBusinessCardWorkspace()
</script>

<style>
@media print {
  body.pixelcore-print-business-card * {
    visibility: hidden !important;
  }

  body.pixelcore-print-business-card .business-card-preview-print,
  body.pixelcore-print-business-card .business-card-preview-print * {
    visibility: visible !important;
  }

  body.pixelcore-print-business-card .business-card-preview-print {
    position: fixed;
    inset: 0;
    display: grid;
    place-items: center;
    background: white;
  }
}
</style>
