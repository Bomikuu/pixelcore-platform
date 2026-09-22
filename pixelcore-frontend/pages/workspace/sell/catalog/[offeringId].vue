<template>
  <section class="workspace-page space-y-5">
    <PageHeader
      :title="offering?.name || 'Catalog item'"
      description="Configure the shared record used by storefront, POS, displays, bookings, inventory, and reports."
    >
      <template #actions>
        <ButtonLink variant="outline"  to="/workspace/sell?view=catalog">Back to catalog</ButtonLink>
        <template v-if="offering">
          <div v-if="confirmingUnpublish" class="flex items-center gap-2 rounded-lg border border-destructive/25 bg-destructive/5 p-1 pl-3">
            <span class="text-xs font-bold text-destructive">Remove from sales channels?</span>
            <Button variant="outline" class="!min-h-8 !px-3" type="button" @click="confirmingUnpublish = false">Keep published</Button>
            <Button variant="ghost" class="inline-flex min-h-8 items-center rounded-md bg-destructive px-3 text-xs font-bold text-destructive-foreground" type="button" :disabled="savingBasics || mediaBusy" @click="saveBasics('draft')">Confirm unpublish</Button>
          </div>
          <Button variant="outline" v-else-if="offering.status === 'published'" class="text-destructive" type="button" :disabled="savingBasics || mediaBusy" @click="confirmingUnpublish = true"><EyeOff class="h-4 w-4" /> Unpublish</Button>
          <Button v-else type="button" :disabled="savingBasics || mediaBusy" @click="saveBasics('published')"><Globe2 class="h-4 w-4" /> Publish</Button>
          <Button type="button" :disabled="savingBasics || mediaBusy" @click="saveBasics(productForm.status)">{{ savingBasics ? 'Saving…' : 'Save changes' }}</Button>
        </template>
      </template>
    </PageHeader>

    <StatePanel v-if="loading" kind="loading" title="Loading offering" message="Retrieving variants, modifiers, costs, and typed details." />
    <StatePanel v-else-if="error" kind="error" title="Offering unavailable" :message="error" />

    <template v-else>
      <Tabs v-model="editorTab" class="min-w-0 space-y-5">
        <div class="overflow-x-auto border-b">
          <TabsList aria-label="Product editor sections" class="flex h-auto w-max min-w-full justify-start rounded-none bg-transparent p-0">
            <TabsTrigger value="details" class="shrink-0 rounded-none border-b-2 border-transparent px-4 py-3 text-muted-foreground hover:bg-muted/60 hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"><span class="inline-flex items-center gap-2"><FileText class="h-4 w-4 shrink-0" aria-hidden="true" /><span>Details</span></span></TabsTrigger>
            <TabsTrigger value="media" :disabled="productForm.offering_type === 'service'" class="shrink-0 rounded-none border-b-2 border-transparent px-4 py-3 text-muted-foreground hover:bg-muted/60 hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"><span class="inline-flex items-center gap-2"><Images class="h-4 w-4 shrink-0" aria-hidden="true" /><span>Gallery & media</span></span></TabsTrigger>
            <TabsTrigger value="options" :disabled="productForm.offering_type === 'service'" class="shrink-0 rounded-none border-b-2 border-transparent px-4 py-3 text-muted-foreground hover:bg-muted/60 hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"><span class="inline-flex items-center gap-2"><Boxes class="h-4 w-4 shrink-0" aria-hidden="true" /><span>Variants</span></span></TabsTrigger>
            <TabsTrigger value="merchandising" :disabled="productForm.offering_type === 'service'" class="shrink-0 rounded-none border-b-2 border-transparent px-4 py-3 text-muted-foreground hover:bg-muted/60 hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"><span class="inline-flex items-center gap-2"><Megaphone class="h-4 w-4 shrink-0" aria-hidden="true" /><span>Organization & SEO</span></span></TabsTrigger>
            <TabsTrigger value="extensions" class="shrink-0 rounded-none border-b-2 border-transparent px-4 py-3 text-muted-foreground hover:bg-muted/60 hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"><span class="inline-flex items-center gap-2"><Wrench class="h-4 w-4 shrink-0" aria-hidden="true" /><span>Extensions</span></span></TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="details" class="mt-0">
          <form class="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]" @submit.prevent="saveBasics(productForm.status)">
            <section class="overflow-hidden rounded-xl border bg-card xl:col-span-2" aria-labelledby="product-image-heading">
              <div class="grid sm:grid-cols-[14rem_minmax(0,1fr)]">
                <div class="flex h-56 items-center justify-center border-b bg-muted/40 p-4 sm:border-b-0 sm:border-r">
                  <img v-if="previewMedia.length" :src="previewMedia[0].url" :alt="previewMedia[0].alt_text || productForm.name" class="h-full w-full object-contain" />
                  <ImageIcon v-else class="h-8 w-8 text-muted-foreground" aria-label="No primary image" />
                </div>
                <div class="min-w-0 p-5 sm:p-6">
                  <div class="flex flex-wrap items-center gap-2"><h2 id="product-image-heading" class="text-base font-extrabold">{{ productForm.offering_type === 'service' ? 'Service image' : 'Primary image' }}</h2><Badge variant="secondary">Listing identity</Badge></div>
                  <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{{ productForm.offering_type === 'service' ? 'The image customers see while choosing a service and booking a visit.' : 'The cover customers recognize in your catalog and shop. Gallery uploads add other views without replacing this image.' }}</p>
                  <div class="mt-4 flex flex-wrap gap-2">
                    <Button type="button" variant="outline" :disabled="savingBasics || mediaBusy" @click="openCoverPicker"><Upload class="h-4 w-4" aria-hidden="true" />{{ previewMedia.length ? 'Replace primary image' : 'Add primary image' }}</Button>
                    <Input id="product-primary-image-input" :key="imageInputKey" class="sr-only" tabindex="-1" aria-label="Upload primary image" type="file" :disabled="savingBasics || mediaBusy" accept="image/jpeg,image/png,image/webp,image/avif" @change="selectImage" />
                    <Button v-if="previewMedia.length" variant="ghost" class="text-destructive" type="button" :disabled="savingBasics || mediaBusy" @click="removeImage"><Trash2 class="h-4 w-4" aria-hidden="true" />Remove</Button>
                    <Button v-if="productForm.offering_type !== 'service'" variant="ghost" type="button" @click="editorTab = 'media'"><Images class="h-4 w-4" aria-hidden="true" />View gallery</Button>
                  </div>
                  <label v-if="imageFile" class="mt-4 block"><span class="field-label">Image description</span><Input v-model.trim="imageAlt" maxlength="250" placeholder="Describe the image for accessibility" /></label>
                  <p class="mt-3 text-xs leading-5 text-muted-foreground">{{ imageFile || imageRemoved ? 'Save changes to apply your primary image update.' : 'JPG, PNG, WebP, or AVIF · Up to 8 MB.' }}</p>
                </div>
              </div>
            </section>
            <div class="min-w-0 space-y-5">
          <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="product-details-heading">
            <div class="flex flex-wrap items-start justify-between gap-3"><div><h2 id="product-details-heading" class="text-base font-extrabold">{{ productForm.offering_type === 'service' ? 'Service information' : 'Product information' }}</h2><p class="mt-1 text-sm text-muted-foreground">{{ productForm.offering_type === 'service' ? 'Edit the customer-facing service used by public booking and the business schedule.' : 'Edit the customer-facing record used across catalog, POS, displays, and checkout.' }}</p></div><StatusPill :value="offering.status" /></div>
            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              <label class="sm:col-span-2"><span class="field-label">Name</span><Input v-model.trim="productForm.name" required maxlength="180" /></label>
              <label><span class="field-label">Type</span><NativeSelect v-model="productForm.offering_type" @change="updateOfferingType"><option value="physical">Physical product</option><option value="digital">Digital product</option><option value="service">Bookable service</option></NativeSelect></label>
              <label><span class="field-label">Category</span><NativeSelect v-model="productForm.category_public_id"><option value="">Uncategorized</option><option v-for="category in categories" :key="category.public_id" :value="category.public_id">{{ category.name }}</option></NativeSelect></label>
              <label class="sm:col-span-2"><span class="field-label">Short summary</span><Input v-model.trim="productForm.summary" maxlength="300" placeholder="A concise benefit customers can scan" /><span class="mt-2 block text-xs text-muted-foreground">{{ productForm.summary.length }}/300 characters</span></label>
              <label class="sm:col-span-2"><span class="field-label">Description</span><Textarea v-model.trim="productForm.description" class="min-h-32 resize-y" maxlength="5000" /></label>
            </div>
          </section>

          <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="pricing-heading">
            <h2 id="pricing-heading" class="text-base font-extrabold">{{ productForm.offering_type === 'service' ? 'Booking details' : 'Pricing, fulfillment & inventory' }}</h2>
            <p class="mt-1 text-sm text-muted-foreground">{{ productForm.offering_type === 'service' ? 'Booking fulfillment is automatic. Assign staff hours and venue resources from Schedule.' : 'These values remain server-authoritative for every sales channel.' }}</p>
            <div class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label><span class="field-label">Price ({{ business.activeBusiness?.currency }})</span><Input v-model="productForm.base_price" type="number" min="0" step="0.01" required /></label>
              <label v-if="productForm.offering_type !== 'service'"><span class="field-label">Compare-at price</span><Input v-model="productForm.compare_at_price" type="number" min="0" step="0.01" placeholder="Optional" /></label>
              <label><span class="field-label">Tax rate (%)</span><Input v-model="productForm.tax_rate" type="number" min="0" max="100" step="0.001" /></label>
              <label v-if="productForm.offering_type !== 'service'"><span class="field-label">SKU</span><Input v-model.trim="productForm.sku" maxlength="80" placeholder="Optional" /></label>
              <label v-if="productForm.offering_type !== 'service'"><span class="field-label">Fulfillment</span><NativeSelect v-model="productForm.fulfillment_type"><option v-if="productForm.offering_type === 'physical'" value="delivery">Delivery</option><option v-if="productForm.offering_type === 'physical'" value="pickup">Pickup</option><option v-if="productForm.offering_type === 'digital'" value="digital">Protected download</option><option value="none">No fulfillment</option></NativeSelect></label>
              <label v-if="productForm.offering_type === 'service'"><span class="field-label">Duration (minutes)</span><Input v-model.number="productForm.duration_minutes" type="number" min="5" max="1440" required /></label>
              <label v-if="productForm.offering_type === 'service'"><span class="field-label">Capacity</span><Input v-model.number="productForm.capacity" type="number" min="1" max="999" /></label>
            </div>
            <label v-if="productForm.offering_type === 'physical'" class="mt-5 flex items-start gap-3"><NativeCheckbox v-model="productForm.track_inventory" class="mt-1 h-4 w-4" /><span><strong class="block text-sm">Track inventory</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Stock balances and reservations will follow this product’s variants.</span></span></label>
          </section>


          <ProductRequestSettings v-if="productForm.offering_type !== 'service'" :profile="profileForm" :eligible="productForm.offering_type === 'physical' && productForm.track_inventory" />
          <section v-if="productForm.offering_type !== 'service'" class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="storefront-presentation-heading">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div><h2 id="storefront-presentation-heading" class="text-base font-extrabold">Storefront presentation</h2><p class="mt-1 text-sm text-muted-foreground">Control how this product appears in the shop and on product cards.</p></div>
              <Button variant="ghost" size="sm" type="button" @click="editorTab = 'media'"><Images class="h-4 w-4" aria-hidden="true" />Manage images</Button>
            </div>
            <div class="mt-5 divide-y">
              <label class="flex items-start justify-between gap-5 py-4 first:pt-0 last:pb-0"><span><strong class="block text-sm">Fullscreen shop highlight</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Give this product the opening screen of the unfiltered shop. Enabling it replaces the previous highlight.</span></span><Switch v-model:checked="profileForm.storefront_highlighted" aria-label="Feature this product in the shop" /></label>
              <label class="flex items-start justify-between gap-5 py-4 first:pt-0 last:pb-0"><span><strong class="block text-sm">Alternate hover image</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Reveal the selected gallery image when a customer hovers the product card.</span></span><Switch v-model:checked="profileForm.card_hover_enabled" aria-label="Enable alternate hover image" /></label>
              <label class="flex items-start justify-between gap-5 py-4 first:pt-0 last:pb-0"><span><strong class="block text-sm">Gallery controls on cards</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Show previous and next controls so customers can browse views without opening the product.</span></span><Switch v-model:checked="profileForm.card_gallery_enabled" aria-label="Enable product card gallery controls" /></label>
            </div>
          </section>
            </div>
            <aside class="min-w-0 xl:sticky xl:top-5">
          <section class="rounded-xl border bg-card p-5" aria-labelledby="record-summary-heading"><div class="flex items-center justify-between gap-3"><h2 id="record-summary-heading" class="text-base font-extrabold">Record summary</h2><ClipboardCheck class="h-5 w-5 text-primary" aria-hidden="true" /></div><dl class="mt-4 divide-y"><div class="flex items-center justify-between gap-4 py-3"><dt class="text-sm text-muted-foreground">Base price</dt><dd class="font-extrabold">{{ money(productForm.base_price) }}</dd></div><div v-if="productForm.offering_type === 'service'" class="flex items-center justify-between gap-4 py-3"><dt class="text-sm text-muted-foreground">Duration</dt><dd class="font-extrabold">{{ productForm.duration_minutes }} min</dd></div><div v-if="productForm.offering_type === 'service'" class="flex items-center justify-between gap-4 py-3"><dt class="text-sm text-muted-foreground">Capacity</dt><dd class="font-extrabold">{{ productForm.capacity }}</dd></div><div v-if="productForm.offering_type !== 'service'" class="flex items-center justify-between gap-4 py-3"><dt class="text-sm text-muted-foreground">Variants</dt><dd class="font-extrabold">{{ variants.length }}</dd></div><div v-if="productForm.offering_type !== 'service'" class="flex items-center justify-between gap-4 py-3"><dt class="text-sm text-muted-foreground">Calculated cost</dt><dd class="font-extrabold">{{ money(offering.calculated_unit_cost) }}</dd></div></dl><p v-if="productForm.offering_type === 'service'" class="mt-3 rounded-lg bg-primary/5 p-3 text-xs leading-5 text-muted-foreground">This service appears in Schedule after it is published.</p><p v-if="productForm.offering_type === 'digital'" class="mt-3 rounded-lg bg-muted p-3 text-xs leading-5 text-muted-foreground">A protected delivery asset is required before a digital product can be published.</p></section>

            </aside>
          </form>
        </TabsContent>
        <TabsContent value="media" class="mt-0 space-y-5">
          <ProductMediaGallery v-if="productForm.offering_type !== 'service'" :items="galleryMedia" :cover="previewMedia[0] || null" :cover-pending="Boolean(imageFile)" :pending="galleryPreviews" :hover="currentHover" :disabled="savingBasics || mediaBusy"
            @select="selectGallery" @set-hover="runGalleryAction(() => setHoverMedia($event))" @clear-hover="runGalleryAction(clearHoverMedia)"
            @remove="runGalleryAction(() => removeGalleryMedia($event))" @remove-pending="removePendingGallery" @edit-cover="editorTab = 'details'" />
          <form class="grid items-start gap-5 lg:grid-cols-2" @submit.prevent="saveBasics(productForm.status)">



          <section v-if="productForm.offering_type !== 'service'" class="rounded-xl border bg-card p-5" aria-labelledby="product-model-heading"><div class="flex items-center justify-between"><h2 id="product-model-heading" class="text-base font-extrabold">3D product view</h2><Box class="h-5 w-5 text-primary" /></div><p class="mt-2 text-xs leading-5 text-muted-foreground">Add one self-contained GLB up to 25 MB and a poster fallback. Models are validated before public exposure.</p><div class="mt-4 space-y-2"><Button as-child variant="outline" class="w-full"><label class="cursor-pointer"><Upload class="h-4 w-4" />{{ modelFile ? modelFile.name : currentModel ? 'Replace 3D model' : 'Add 3D model' }}<Input class="sr-only" type="file" accept=".glb,model/gltf-binary" @change="selectModel" /></label></Button><Button as-child variant="outline" class="w-full"><label class="cursor-pointer"><ImageIcon class="h-4 w-4" />{{ posterFile ? posterFile.name : currentPoster ? 'Replace poster' : 'Add poster fallback' }}<Input class="sr-only" type="file" accept="image/jpeg,image/png,image/webp,image/avif" @change="selectPoster" /></label></Button></div><Badge v-if="currentModel" class="mt-4" :variant="currentModel.processing_status === 'ready' ? 'default' : 'secondary'">Model {{ currentModel.processing_status }}</Badge></section>


          </form>
        </TabsContent>
        <TabsContent value="options" class="mt-0 min-w-0 space-y-5">
    <section v-if="productForm.offering_type !== 'service'" class="rounded-xl border bg-card p-5 sm:p-6"><div class="flex flex-wrap items-start justify-between gap-4"><div><h2 class="text-base font-extrabold">Options and variant matrix</h2><p class="mt-2 text-sm leading-6 text-muted-foreground">Build up to three reusable dimensions and 100 purchasable combinations.</p></div><div class="flex gap-2"><Button variant="outline" type="button" :disabled="matrixDimensions.length >= 3" @click="addDimension"><Plus class="h-4 w-4" /> Add dimension</Button><Button type="button" :disabled="savingMatrix || !matrixRows.length" @click="saveMatrix">{{ savingMatrix ? 'Saving matrix…' : 'Save matrix' }}</Button></div></div><div class="mt-5 grid gap-3 md:grid-cols-3"><div v-for="(dimension, index) in matrixDimensions" :key="index" class="rounded-lg border p-4"><div class="flex items-center gap-2"><Input v-model.trim="dimension.name" :aria-label="`Dimension ${index + 1} name`" placeholder="Size" /><Button variant="ghost" size="icon" type="button" aria-label="Remove dimension" @click="removeDimension(index)"><Trash2 class="h-4 w-4" /></Button></div><NativeSelect v-model="dimension.display_type" class="mt-2"><option value="text">Text values</option><option value="color">Color swatches</option></NativeSelect><Textarea v-model.trim="dimension.valueText" class="mt-2 min-h-20" placeholder="Small, Medium, Large" :aria-label="`${dimension.name || 'Dimension'} values`" /></div></div><div class="mt-6 overflow-x-auto"><Table><TableHeader><TableRow><TableHead>Combination</TableHead><TableHead>SKU</TableHead><TableHead>Barcode</TableHead><TableHead>Price</TableHead><TableHead>Compare at</TableHead><TableHead>Cost</TableHead><TableHead>Active</TableHead></TableRow></TableHeader><TableBody><TableRow v-for="row in matrixRows" :key="row.key"><TableCell class="min-w-44 font-bold">{{ Object.values(row.options).join(' / ') }}</TableCell><TableCell><Input v-model.trim="row.sku" class="min-w-32" aria-label="SKU" /></TableCell><TableCell><Input v-model.trim="row.barcode" class="min-w-32" aria-label="Barcode" /></TableCell><TableCell><Input v-model="row.price" class="min-w-28" type="number" min="0" step="0.01" aria-label="Price" /></TableCell><TableCell><Input v-model="row.compare_at_price" class="min-w-28" type="number" min="0" step="0.01" aria-label="Compare-at price" /></TableCell><TableCell><Input v-model="row.unit_cost" class="min-w-28" type="number" min="0" step="0.01" aria-label="Unit cost" /></TableCell><TableCell><Switch v-model:checked="row.is_active" :aria-label="`Activate ${Object.values(row.options).join(' ')}`" /></TableCell></TableRow><TableEmpty v-if="!matrixRows.length" :colspan="7">Add a dimension and comma-separated values to generate combinations.</TableEmpty></TableBody></Table></div></section>

    <section v-if="colorDimensions.length" class="rounded-xl border bg-card p-5 sm:p-6"><h2 class="text-base font-extrabold">Color swatches</h2><p class="mt-2 text-sm text-muted-foreground">Choose the storefront swatch for every color value.</p><div class="mt-4 flex flex-wrap gap-4"><template v-for="dimension in colorDimensions" :key="dimension.name"><label v-for="value in dimension.valueText.split(',').map((item) => item.trim()).filter(Boolean)" :key="`${dimension.name}-${value}`" class="flex items-center gap-3 rounded-lg border px-3 py-2 text-sm font-semibold"><Input v-model="dimension.colors[value]" class="h-8 w-10 p-1" type="color" :aria-label="`${value} color swatch`" />{{ value }}</label></template></div></section>


          <form v-if="productForm.offering_type === 'physical'" class="rounded-xl border bg-card p-5 sm:p-6" @submit.prevent="saveBasics(productForm.status)">
            <h2 class="text-base font-extrabold">Shipping details</h2>
            <p class="mt-1 text-sm text-muted-foreground">Package weight and dimensions for this product. Save these with Save changes.</p>
            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              <label><span class="field-label">Shipping weight (grams)</span><Input v-model.number="profileForm.shipping_weight_grams" type="number" min="0" /></label>
              <label><span class="field-label">Dimensions</span><Input v-model.trim="shippingDimensions" placeholder="length: 30, width: 20, unit: cm" /></label>
            </div>
          </form>
        </TabsContent>
        <TabsContent value="merchandising" class="mt-0">
          <form class="space-y-5" @submit.prevent="saveBasics(productForm.status)">
          <section v-if="productForm.offering_type !== 'service'" class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="merchandising-heading">
            <h2 id="merchandising-heading" class="text-base font-extrabold">Brand & collections</h2><p class="mt-1 text-sm text-muted-foreground">Shape how customers discover and understand this product.</p>
            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              <label><span class="field-label">Brand</span><Input v-model.trim="profileForm.brand" maxlength="140" /></label>
              <label><span class="field-label">Tags</span><Input v-model.trim="profileTags" placeholder="new, essentials, gift" /></label>
              <label class="sm:col-span-2"><span class="field-label">Collections</span><div class="grid gap-2 rounded-lg border p-3 sm:grid-cols-2"><label v-for="collection in collections" :key="collection.public_id" class="flex items-center gap-2 text-sm"><NativeCheckbox v-model="selectedCollectionIds" :value="collection.public_id" />{{ collection.name }}</label><span v-if="!collections.length" class="text-sm text-muted-foreground">No collections yet. Create one in Sell → Collections, then assign this product here.</span></div></label>
              <label class="sm:col-span-2"><span class="field-label">Materials</span><Textarea v-model.trim="profileForm.materials" class="min-h-24" /></label>
              <label class="sm:col-span-2"><span class="field-label">Care instructions</span><Textarea v-model.trim="profileForm.care_instructions" class="min-h-24" /></label>
            </div>
          </section>

          <section v-if="productForm.offering_type !== 'service'" class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="product-seo-heading">
            <h2 id="product-seo-heading" class="text-base font-extrabold">Specifications & search appearance</h2><p class="mt-1 text-sm text-muted-foreground">Use one key and value per line for structured details shown on the product page.</p>
            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              <label><span class="field-label">Specifications</span><Textarea v-model.trim="specificationLines" class="min-h-28" placeholder="Fabric: Cotton&#10;Origin: Philippines" /></label>
              <label><span class="field-label">Size guide</span><Textarea v-model.trim="sizeGuideLines" class="min-h-28" placeholder="Small: 91–96 cm&#10;Medium: 97–102 cm" /></label>
              <label class="sm:col-span-2"><span class="field-label">SEO title</span><Input v-model.trim="profileForm.seo_title" maxlength="70" /><span class="mt-1 block text-xs text-muted-foreground">{{ profileForm.seo_title.length }}/70</span></label>
              <label class="sm:col-span-2"><span class="field-label">SEO description</span><Textarea v-model.trim="profileForm.seo_description" maxlength="170" /><span class="mt-1 block text-xs text-muted-foreground">{{ profileForm.seo_description.length }}/170</span></label>
            </div>
          </section>

          </form>
        </TabsContent>
        <TabsContent value="extensions" class="mt-0">
    <div class="grid gap-6 xl:grid-cols-2">

      <section class="rounded-xl border bg-card p-5 sm:p-6">
        <h2 class="text-base font-extrabold">Modifiers and options</h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">Option groups work for sizes, add-ons, finishes, service extras, or food modifiers.</p>
        <div v-for="group in groups" :key="group.public_id" class="mt-5 border-y py-4">
          <div class="flex justify-between gap-4">
            <strong>{{ group.name }}</strong>
            <span class="text-xs text-muted-foreground">{{ group.minimum_choices }}–{{ group.maximum_choices }}</span>
          </div>
          <ul class="mt-3 space-y-2 text-sm">
            <li v-for="option in group.options" :key="option.public_id" class="flex justify-between gap-4">
              <span>{{ option.name }}</span>
              <span>{{ option.price_delta ? `+${money(option.price_delta)}` : 'Included' }}</span>
            </li>
          </ul>
          <form class="mt-4 flex gap-2" @submit.prevent="addOption(group)">
            <Input v-model.trim="optionDrafts[group.public_id]" :aria-label="`New option for ${group.name}`" placeholder="Option name" maxlength="120" required />
            <Button variant="outline" type="submit">Add</Button>
          </form>
        </div>
        <form class="mt-6 space-y-3 border-t pt-5" @submit.prevent="addGroup">
          <label class="field-label">Group name<Input v-model.trim="groupForm.name" class="mt-1" maxlength="120" required /></label>
          <div class="grid grid-cols-2 gap-3">
            <label class="field-label">Minimum<Input v-model.number="groupForm.minimum_choices" class="mt-1" type="number" min="0" /></label>
            <label class="field-label">Maximum<Input v-model.number="groupForm.maximum_choices" class="mt-1" type="number" min="1" /></label>
          </div>
          <Button variant="outline" class="w-full">Add option group</Button>
        </form>
      </section>

      <section class="rounded-xl border bg-card p-5 sm:p-6">
        <h2 class="text-base font-extrabold">Cost components</h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">Actual component costs roll into gross profit reports without becoming food-specific.</p>
        <div v-if="costs.length" class="mt-5 divide-y border-y">
          <div v-for="cost in costs" :key="cost.public_id" class="flex justify-between gap-4 py-3 text-sm">
            <span>{{ cost.quantity }} {{ cost.unit }} · {{ cost.name }}</span>
            <strong>{{ money(cost.extended_cost) }}</strong>
          </div>
        </div>
        <form class="mt-6 space-y-3" @submit.prevent="addCost">
          <label class="field-label">Component or ingredient<Input v-model.trim="costForm.name" class="mt-1" required /></label>
          <div class="grid grid-cols-3 gap-2">
            <Input v-model.number="costForm.quantity" type="number" min="0.001" step="0.001" aria-label="Quantity" required />
            <Input v-model.trim="costForm.unit" placeholder="unit" aria-label="Unit" required />
            <Input v-model.number="costForm.unit_cost" type="number" min="0" step="0.01" aria-label="Unit cost" required />
          </div>
          <Button variant="outline" class="w-full">Add cost component</Button>
        </form>
      </section>

      <section class="rounded-xl border bg-card p-5 sm:p-6">
        <template v-if="isRestaurant">
          <h2 class="text-base font-extrabold">Food profile</h2>
          <p class="mt-2 text-sm leading-6 text-muted-foreground">Restaurant-only typed details stay optional and never alter the generic offering contract.</p>
          <form class="mt-5 space-y-4" @submit.prevent="saveFood">
            <label class="field-label">Serving label<Input v-model.trim="foodForm.serving_label" class="mt-1" /></label>
            <label class="field-label">Calories<Input v-model.number="foodForm.calories" class="mt-1" type="number" min="0" /></label>
            <div class="grid grid-cols-3 gap-2">
              <label class="field-label">Protein g<Input v-model.number="foodForm.protein_grams" class="mt-1" type="number" min="0" step="0.01" /></label>
              <label class="field-label">Carbs g<Input v-model.number="foodForm.carbohydrate_grams" class="mt-1" type="number" min="0" step="0.01" /></label>
              <label class="field-label">Fat g<Input v-model.number="foodForm.fat_grams" class="mt-1" type="number" min="0" step="0.01" /></label>
            </div>
            <label class="field-label">Allergens, comma separated<Input v-model.trim="foodAllergens" class="mt-1" /></label>
            <label class="field-label">Ingredients<Textarea v-model.trim="foodForm.ingredients" class="mt-1 min-h-28"></Textarea></label>
            <Button class="w-full">Save food profile</Button>
          </form>
        </template>
        <template v-else>
          <h2 class="text-base font-extrabold">Typed extensions</h2>
          <p class="mt-4 leading-7 text-muted-foreground">This {{ business.activeBusiness?.industry_preset }} business uses the generic offering record. Switch the business preset to Restaurant if this item needs nutrition, allergens, recipe components, and Poster Menu vocabulary.</p>
        </template>
      </section>
    </div>


        </TabsContent>
      </Tabs>
      <p v-if="message" class="border-t pt-4 text-sm" :class="messageTone" role="status">{{ message }}</p>
    </template>
  </section>
</template>

<script setup>
import { resolveProductCover } from '~/utils/productImages'
import ProductMediaGallery from '~/components/storefront/ProductMediaGallery.vue'
import ProductRequestSettings from '~/components/storefront/ProductRequestSettings.vue'
import { Box, Boxes, ClipboardCheck, EyeOff, FileText, Globe2, ImageIcon, Images, Megaphone, Plus, Trash2, Upload, Wrench } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'

const route = useRoute()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const offering = ref(null)
const variants = ref([])
const groups = ref([])
const costs = ref([])
const categories = ref([])
const collections = ref([])
const loading = ref(true)
const error = ref('')
const message = ref('')
const messageTone = ref('text-primary')
const savingBasics = ref(false)
const savingVariant = ref(false)
const savingMatrix = ref(false)
const editorTab = ref('details')
const confirmingUnpublish = ref(false)
const imageFile = ref(null)
const imagePreview = ref('')
const imageAlt = ref('')
const imageRemoved = ref(false)
const imageInputKey = ref(0)
const modelFile = ref(null)
const posterFile = ref(null)
const galleryFiles = ref([])
const galleryPreviews = ref([])
const mediaBusy = ref(false)

watch(galleryFiles, (files) => {
  galleryPreviews.value.forEach((item) => URL.revokeObjectURL(item.url))
  galleryPreviews.value = files.map((file) => ({ name: file.name, url: URL.createObjectURL(file) }))
}, { flush: 'sync' })

function removePendingGallery(index) {
  galleryFiles.value = galleryFiles.value.filter((_, position) => position !== index)
}

async function runGalleryAction(action) {
  if (mediaBusy.value || savingBasics.value) return
  mediaBusy.value = true
  try { await action() }
  catch (requestError) { setMessage(requestError?.data?.error?.message || 'The gallery could not be updated. Try again.', true) }
  finally { mediaBusy.value = false }
}
const selectedCollectionIds = ref([])
const profileTags = ref('')
const shippingDimensions = ref('')
const specificationLines = ref('')
const sizeGuideLines = ref('')
const profileForm = reactive({ brand: '', materials: '', care_instructions: '', shipping_weight_grams: null, seo_title: '', seo_description: '', card_hover_enabled: true, card_gallery_enabled: false, storefront_highlighted: false, reservation_enabled: false, rental_enabled: false, reservation_terms: '', rental_terms: '' })
const matrixDimensions = ref([])
const matrixRows = ref([])
const optionDrafts = reactive({})
const productForm = reactive({ category_public_id: '', name: '', summary: '', description: '', offering_type: 'physical', status: 'draft', fulfillment_type: 'delivery', base_price: '', compare_at_price: '', tax_rate: '0', sku: '', track_inventory: true, duration_minutes: 60, capacity: 1, metadata: {} })
const variantForm = reactive({ name: '', sku: '', price: 0, unit_cost: 0, attributes: {}, is_active: true, sort_order: 0 })
const groupForm = reactive({ name: '', minimum_choices: 0, maximum_choices: 1, is_required: false, sort_order: 0 })
const costForm = reactive({ name: '', quantity: 1, unit: 'unit', unit_cost: 0 })
const foodForm = reactive({ serving_label: '', calories: null, protein_grams: null, carbohydrate_grams: null, fat_grams: null, ingredients: '' })
const foodAllergens = ref('')
const isRestaurant = computed(() => business.activeBusiness?.industry_preset === 'restaurant')
const currentImage = computed(() => resolveProductCover(offering.value))
const currentModel = computed(() => offering.value?.ordered_media?.find((item) => item.role === 'model') || null)
const currentPoster = computed(() => offering.value?.ordered_media?.find((item) => item.role === 'poster') || null)
const currentHover = computed(() => offering.value?.ordered_media?.find((item) => item.role === 'hover') || null)
const galleryMedia = computed(() => offering.value?.ordered_media?.filter((item) => item.role === 'gallery') || [])
const colorDimensions = computed(() => matrixDimensions.value.filter((dimension) => dimension.display_type === 'color'))
const previewMedia = computed(() => {
  if (imagePreview.value) return [{ url: imagePreview.value, alt_text: imageAlt.value }]
  if (imageRemoved.value) return []
  return currentImage.value ? [currentImage.value] : []
})

onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses()
  await load()
})

async function load() {
  const id = business.activeBusiness.public_id
  try {
    const [item, groupResponse, costResponse, categoryResponse, collectionResponse] = await Promise.all([
      apiFetch(`businesses/${id}/offerings/${route.params.offeringId}/`),
      apiFetch(`businesses/${id}/option-groups/`),
      apiFetch(`businesses/${id}/offering-costs/`),
      apiFetch(`businesses/${id}/categories/?page_size=100`),
      apiFetch(`businesses/${id}/collections/?page_size=100`),
    ])
    offering.value = item
    syncProductForm(item)
    variants.value = item.variants || []
    groups.value = (groupResponse.results || []).filter((group) => group.offering_public_id === route.params.offeringId)
    costs.value = (costResponse.results || []).filter((cost) => cost.offering_public_id === route.params.offeringId)
    categories.value = categoryResponse.results || []
    collections.value = collectionResponse.results || []
    selectedCollectionIds.value = (item.collections || []).map((collection) => collection.public_id)
    syncProfile(item.product_profile || {})
    syncMatrix(item)
    Object.assign(variantForm, { price: item.base_price })
    if (item.food_profile) {
      Object.assign(foodForm, item.food_profile)
      foodAllergens.value = (item.food_profile.allergens || []).join(', ')
    }
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || 'The offering could not be loaded.'
  } finally {
    loading.value = false
  }
}

function syncProductForm(item) {
  Object.assign(productForm, {
    category_public_id: item.category_public_id || '',
    name: item.name || '',
    summary: item.summary || '',
    description: item.description || '',
    offering_type: item.offering_type || 'physical',
    status: item.status || 'draft',
    fulfillment_type: item.fulfillment_type || 'none',
    base_price: item.base_price ?? '',
    compare_at_price: item.compare_at_price ?? '',
    tax_rate: item.tax_rate ?? '0',
    sku: item.sku || '',
    track_inventory: Boolean(item.track_inventory),
    duration_minutes: item.duration_minutes || 60,
    capacity: item.capacity || 1,
    metadata: item.metadata || {},
  })
  imageAlt.value = resolveProductCover(item)?.alt_text || ''
}

function objectToLines(value) { return Object.entries(value || {}).map(([key, item]) => `${key}: ${item}`).join('\n') }
function linesToObject(value) { return Object.fromEntries(String(value || '').split(/\n|,/).map((line) => line.split(':')).filter((parts) => parts.length > 1 && parts[0].trim()).map(([key, ...rest]) => [key.trim(), rest.join(':').trim()])) }
function syncProfile(profile) {
  Object.assign(profileForm, { reservation_enabled: Boolean(profile.reservation_enabled), rental_enabled: Boolean(profile.rental_enabled), reservation_terms: profile.reservation_terms || '', rental_terms: profile.rental_terms || '' })
  Object.assign(profileForm, { brand: profile.brand || '', materials: profile.materials || '', care_instructions: profile.care_instructions || '', shipping_weight_grams: profile.shipping_weight_grams ?? null, seo_title: profile.seo_title || '', seo_description: profile.seo_description || '', card_hover_enabled: profile.card_hover_enabled !== false, card_gallery_enabled: Boolean(profile.card_gallery_enabled), storefront_highlighted: Boolean(profile.storefront_highlighted) })
  profileTags.value = (profile.tags || []).join(', ')
  shippingDimensions.value = objectToLines(profile.shipping_dimensions)
  specificationLines.value = objectToLines(profile.specifications)
  sizeGuideLines.value = objectToLines(profile.size_guide)
}

function syncMatrix(item) {
  matrixDimensions.value = (item.variant_dimensions || []).map((dimension) => ({ name: dimension.name, display_type: dimension.display_type, valueText: dimension.values.map((value) => value.label).join(', '), colors: Object.fromEntries(dimension.values.map((value) => [value.label, value.swatch_color])) }))
  rebuildMatrix(item.variants || [])
}

function addDimension() { matrixDimensions.value.push({ name: '', display_type: 'text', valueText: '', colors: {} }) }
function removeDimension(index) { matrixDimensions.value.splice(index, 1); rebuildMatrix() }
function cartesian(groups) { return groups.reduce((rows, group) => rows.flatMap((row) => group.map((value) => [...row, value])), [[]]) }
function rebuildMatrix(source = matrixRows.value) {
  const dimensions = matrixDimensions.value.map((dimension) => ({ ...dimension, values: dimension.valueText.split(',').map((value) => value.trim()).filter(Boolean) })).filter((dimension) => dimension.name && dimension.values.length)
  if (!dimensions.length) { matrixRows.value = []; return }
  const existing = new Map(source.map((row) => [row.key || Object.values(row.attributes || row.options || {}).join('|'), row]))
  matrixRows.value = cartesian(dimensions.map((dimension) => dimension.values)).slice(0, 100).map((values, index) => {
    const options = Object.fromEntries(dimensions.map((dimension, dimensionIndex) => [dimension.name, values[dimensionIndex]]))
    const key = values.join('|')
    const matched = existing.get(key) || source.find((variant) => dimensions.every((dimension) => variant.attributes?.[dimension.name] === options[dimension.name])) || {}
    return { key, public_id: matched.public_id, options, sku: matched.sku || '', barcode: matched.barcode || '', price: matched.price ?? productForm.base_price, compare_at_price: matched.compare_at_price || '', unit_cost: matched.unit_cost || 0, is_active: matched.is_active !== false }
  })
}

watch(matrixDimensions, () => rebuildMatrix(), { deep: true })

function updateOfferingType() {
  productForm.fulfillment_type = productForm.offering_type === 'physical' ? 'delivery' : productForm.offering_type === 'digital' ? 'digital' : 'booking'
  if (productForm.offering_type === 'service') {
    productForm.compare_at_price = ''
    productForm.sku = ''
    productForm.track_inventory = false
    if (['media', 'options', 'merchandising'].includes(editorTab.value)) editorTab.value = 'details'
  } else {
    productForm.capacity = 1
  }
}

function openCoverPicker() { document.getElementById('product-primary-image-input')?.click() }

function selectImage(event) {
  const file = event.target.files?.[0] || null
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp', 'image/avif'].includes(file.type) || file.size > 8 * 1024 * 1024) {
    setMessage('Choose a JPG, PNG, WebP, or AVIF image no larger than 8 MB.', true)
    imageInputKey.value += 1
    return
  }
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
  imageAlt.value = currentImage.value?.alt_text || ''
  imageRemoved.value = false
  setMessage('')
}

function removeImage() {
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imageFile.value = null
  imagePreview.value = ''
  imageAlt.value = ''
  imageRemoved.value = true
  imageInputKey.value += 1
}

async function uploadImage() {
  if (!imageFile.value) return null
  const body = new FormData()
  body.append('title', productForm.name || imageFile.value.name)
  body.append('alt_text', imageAlt.value)
  body.append('asset_type', 'image')
  body.append('file', imageFile.value)
  const asset = await apiFetch(`businesses/${business.activeBusiness.public_id}/assets/`, { method: 'POST', body })
  return asset.public_id
}

function selectModel(event) { const file = event.target.files?.[0]; if (!file) return; if (!file.name.toLowerCase().endsWith('.glb') || file.size > 25 * 1024 * 1024) return setMessage('Choose one self-contained GLB no larger than 25 MB.', true); modelFile.value = file }
function selectPoster(event) { const file = event.target.files?.[0]; if (!file) return; if (!['image/jpeg', 'image/png', 'image/webp', 'image/avif'].includes(file.type) || file.size > 8 * 1024 * 1024) return setMessage('Choose a JPG, PNG, WebP, or AVIF poster no larger than 8 MB.', true); posterFile.value = file }
function selectGallery(event) {
  const files = [...(event.target.files || [])]
  event.target.value = ''
  if (!files.length) return
  if (files.some((file) => !['image/jpeg', 'image/png', 'image/webp', 'image/avif'].includes(file.type) || file.size > 8 * 1024 * 1024)) {
    return setMessage('Every gallery image must be JPG, PNG, WebP, or AVIF and no larger than 8 MB.', true)
  }
  if (galleryFiles.value.length + files.length > 12) {
    return setMessage('You can add up to 12 gallery images per save. Save or remove selected images before adding more.', true)
  }
  galleryFiles.value = [...galleryFiles.value, ...files]
}
async function uploadAsset(file, assetType, altText = '') { const body = new FormData(); body.append('title', file.name); body.append('alt_text', altText); body.append('asset_type', assetType); body.append('file', file); return apiFetch(`businesses/${business.activeBusiness.public_id}/assets/`, { method: 'POST', body }) }
async function replaceMedia(role, file, assetType, altText = '') { if (!file) return; const current = offering.value.ordered_media?.find((item) => item.role === role); if (current) await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/${current.public_id}/`, { method: 'DELETE' }); const asset = await uploadAsset(file, assetType, altText); if (asset.processing_status === 'rejected') throw new Error(asset.validation_error || 'The uploaded model was rejected.'); await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/`, { method: 'POST', body: { asset_public_id: asset.public_id, role, sort_order: role === 'cover' ? 0 : 1 } }) }
async function assignExistingMedia(role, assetPublicId) { const current = offering.value.ordered_media?.find((item) => item.role === role); if (current) await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/${current.public_id}/`, { method: 'DELETE' }); await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/`, { method: 'POST', body: { asset_public_id: assetPublicId, role, sort_order: 0 } }) }
async function addGalleryMedia() { for (const [index, file] of galleryFiles.value.entries()) { const asset = await uploadAsset(file, 'image', `${productForm.name} product view`); await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/`, { method: 'POST', body: { asset_public_id: asset.public_id, role: 'gallery', sort_order: galleryMedia.value.length + index + 1 } }) } }
async function refreshOffering() { offering.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/`) }
async function clearHoverMedia() { if (!currentHover.value) return; await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/${currentHover.value.public_id}/`, { method: 'DELETE' }); await refreshOffering(); setMessage('Product card hover image cleared.') }
async function setHoverMedia(item) { if (currentHover.value?.asset_public_id === item.asset_public_id) return; if (currentHover.value) await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/${currentHover.value.public_id}/`, { method: 'DELETE' }); await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/`, { method: 'POST', body: { asset_public_id: item.asset_public_id, role: 'hover', sort_order: 1 } }); await refreshOffering(); setMessage('Alternate card image selected.') }
async function removeGalleryMedia(item) { if (currentHover.value?.asset_public_id === item.asset_public_id) await clearHoverMedia(); await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/${item.public_id}/`, { method: 'DELETE' }); offering.value.ordered_media = offering.value.ordered_media.filter((media) => media.public_id !== item.public_id); setMessage('Gallery image removed.') }

async function saveBasics(targetStatus) {
  if (savingBasics.value || mediaBusy.value) return
  if (!productForm.name || productForm.base_price === '') {
    setMessage('Add a product name and price before saving.', true)
    return
  }
  savingBasics.value = true
  setMessage('')
  try {
    const uploadedAssetId = await uploadImage()
    const retainedAssetIds = offering.value.asset_public_ids || offering.value.media?.map((asset) => asset.public_id) || []
    const payload = {
      ...productForm,
      product_profile: productForm.offering_type === 'service' ? undefined : { ...profileForm, shipping_weight_grams: profileForm.shipping_weight_grams || null, tags: profileTags.value.split(',').map((item) => item.trim()).filter(Boolean), shipping_dimensions: linesToObject(shippingDimensions.value), specifications: linesToObject(specificationLines.value), size_guide: linesToObject(sizeGuideLines.value) },
      status: targetStatus,
      category_public_id: productForm.category_public_id || null,
      compare_at_price: productForm.compare_at_price || null,
      asset_public_ids: uploadedAssetId ? [uploadedAssetId] : imageRemoved.value ? [] : retainedAssetIds,
    }
    if (productForm.offering_type !== 'service') {
      delete payload.duration_minutes
      payload.capacity = 1
    } else {
      payload.fulfillment_type = 'booking'
      payload.compare_at_price = null
      payload.sku = ''
      payload.track_inventory = false
    }
    const updated = await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/`, { method: 'PATCH', body: payload })
    if (uploadedAssetId) await assignExistingMedia('cover', uploadedAssetId)
    if (imageRemoved.value && !uploadedAssetId) { const cover = offering.value.ordered_media?.find((item) => item.role === 'cover'); if (cover) await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/media/${cover.public_id}/`, { method: 'DELETE' }) }
    if (modelFile.value) await replaceMedia('model', modelFile.value, 'model')
    if (posterFile.value) await replaceMedia('poster', posterFile.value, 'image', `${productForm.name} 3D preview`)
    if (galleryFiles.value.length) await addGalleryMedia()
    await Promise.all(collections.value.map((collection) => {
      const ids = new Set((collection.offering_public_ids || []).map(String))
      if (selectedCollectionIds.value.includes(collection.public_id)) ids.add(String(offering.value.public_id)); else ids.delete(String(offering.value.public_id))
      return apiFetch(`businesses/${business.activeBusiness.public_id}/collections/${collection.public_id}/`, { method: 'PATCH', body: { offering_public_ids: [...ids] } })
    }))
    const refreshed = await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/`)
    offering.value = refreshed
    variants.value = refreshed.variants || variants.value
    syncProductForm(refreshed)
    if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
    imageFile.value = null
    imagePreview.value = ''
    imageRemoved.value = false
    imageInputKey.value += 1
    modelFile.value = null
    posterFile.value = null
    galleryFiles.value = []
    confirmingUnpublish.value = false
    setMessage(targetStatus === 'published' ? 'Product saved and published.' : offering.value.status === 'draft' ? 'Product saved as a draft.' : 'Product changes saved.')
  } catch (requestError) {
    setMessage(requestError?.data?.error?.message || 'The product could not be saved. Review the details and try again.', true)
  } finally {
    savingBasics.value = false
  }
}

async function saveMatrix() {
  savingMatrix.value = true
  try {
    const dimensions = matrixDimensions.value.map((dimension, index) => ({ name: dimension.name, display_type: dimension.display_type, sort_order: index, values: dimension.valueText.split(',').map((value, valueIndex) => ({ label: value.trim(), swatch_color: dimension.display_type === 'color' ? (dimension.colors?.[value.trim()] || '') : '', sort_order: valueIndex })).filter((value) => value.label) })).filter((dimension) => dimension.name && dimension.values.length)
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/variant-matrix/`, { method: 'PUT', body: { dimensions, variants: matrixRows.value } })
    variants.value = response.variants
    syncMatrix({ variant_dimensions: response.dimensions, variants: response.variants })
    setMessage('Variant matrix saved.')
  } catch (requestError) { setMessage(requestError?.data?.error?.message || requestError?.message || 'The variant matrix could not be saved.', true) } finally { savingMatrix.value = false }
}

async function addVariant() {
  savingVariant.value = true
  setMessage('')
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/offerings/${offering.value.public_id}/variants/`, {
      method: 'POST',
      body: variantForm,
    })
    variants.value.push(created)
    Object.assign(variantForm, { name: '', sku: '', price: offering.value.base_price, unit_cost: 0, attributes: {}, is_active: true, sort_order: variants.value.length })
    setMessage('Variant added.')
  } catch (requestError) {
    setMessage(requestError?.data?.error?.message || 'The variant could not be added.', true)
  } finally {
    savingVariant.value = false
  }
}

async function addGroup() {
  setMessage('')
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/option-groups/`, {
      method: 'POST',
      body: { ...groupForm, offering_public_id: offering.value.public_id },
    })
    groups.value.push(created)
    groupForm.name = ''
    setMessage('Option group added.')
  } catch (requestError) {
    setMessage(requestError?.data?.error?.message || 'The option group could not be added.', true)
  }
}

async function addOption(group) {
  setMessage('')
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/offering-options/`, {
      method: 'POST',
      body: { group_public_id: group.public_id, name: optionDrafts[group.public_id], price_delta: 0, cost_delta: 0, is_active: true, sort_order: group.options.length },
    })
    group.options.push(created)
    optionDrafts[group.public_id] = ''
    setMessage('Option added.')
  } catch (requestError) {
    setMessage(requestError?.data?.error?.message || 'The option could not be added.', true)
  }
}

async function addCost() {
  setMessage('')
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/offering-costs/`, {
      method: 'POST',
      body: { ...costForm, offering_public_id: offering.value.public_id },
    })
    costs.value.push(created)
    Object.assign(costForm, { name: '', quantity: 1, unit: 'unit', unit_cost: 0 })
    setMessage('Cost component added.')
  } catch (requestError) {
    setMessage(requestError?.data?.error?.message || 'The cost component could not be added.', true)
  }
}

async function saveFood() {
  setMessage('')
  try {
    const body = {
      ...foodForm,
      offering_public_id: offering.value.public_id,
      allergens: foodAllergens.value.split(',').map((item) => item.trim()).filter(Boolean),
    }
    const existing = offering.value.food_profile
    offering.value.food_profile = await apiFetch(existing
      ? `businesses/${business.activeBusiness.public_id}/food-profiles/${existing.public_id}/`
      : `businesses/${business.activeBusiness.public_id}/food-profiles/`, {
      method: existing ? 'PATCH' : 'POST',
      body,
    })
    setMessage('Food profile saved.')
  } catch (requestError) {
    setMessage(requestError?.data?.error?.message || 'The food profile could not be saved.', true)
  }
}

function setMessage(value, isError = false) {
  message.value = value
  messageTone.value = isError ? 'text-destructive' : 'text-primary'
  if (value) {
    toast({
      title: isError ? 'Action failed' : 'Changes saved',
      description: value,
      variant: isError ? 'destructive' : 'default',
      duration: isError ? 6000 : 4000,
    })
  }
}

const money = (value) => new Intl.NumberFormat('en-PH', {
  style: 'currency',
  currency: business.activeBusiness?.currency || 'PHP',
}).format(Number(value || 0))

onBeforeUnmount(() => {
  galleryPreviews.value.forEach((item) => URL.revokeObjectURL(item.url))
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
})
</script>
