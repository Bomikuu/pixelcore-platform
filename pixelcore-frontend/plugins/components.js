import BrandPreview from '~/components/business/BrandPreview.vue'
import BusinessIdentityForm from '~/components/business/BusinessIdentityForm.vue'
import InteractiveDisplayCanvas from '~/components/display/InteractiveDisplayCanvas.vue'
import OrderTotals from '~/components/pos/OrderTotals.vue'
import PairingCodeDisplay from '~/components/pos/PairingCodeDisplay.vue'
import OrderQueueStation from '~/components/pos/OrderQueueStation.vue'
import DevicePairingPanel from '~/components/pos/DevicePairingPanel.vue'
import LivingPixelCore from '~/components/landing/LivingPixelCore.vue'
import SiteBlockRenderer from '~/components/site/SiteBlockRenderer.vue'
import StorefrontFrame from '~/components/site/StorefrontFrame.vue'
import StorefrontHeader from '~/components/site/StorefrontHeader.vue'
import StorefrontPage from '~/components/site/StorefrontPage.vue'
import ThreeScene from '~/components/site/ThreeScene.vue'
import CartDrawer from '~/components/storefront/CartDrawer.vue'
import ProductCard from '~/components/storefront/ProductCard.vue'
import ProductViewer from '~/components/storefront/ProductViewer.vue'
import CollectionEditor from '~/components/storefront/CollectionEditor.vue'
import PageHeader from '~/components/workspace/PageHeader.vue'
import OrderNotifications from '~/components/workspace/OrderNotifications.vue'
import ProductArtwork from '~/components/workspace/ProductArtwork.vue'
import RevenueChart from '~/components/workspace/RevenueChart.vue'
import StaffSelect from '~/components/workspace/StaffSelect.vue'
import StatePanel from '~/components/workspace/StatePanel.vue'
import StatusPill from '~/components/workspace/StatusPill.vue'

const components = {
  BrandPreview,
  BusinessIdentityForm,
  InteractiveDisplayCanvas,
  OrderTotals,
  PairingCodeDisplay,
  OrderQueueStation,
  DevicePairingPanel,
  LivingPixelCore,
  PageHeader,
  OrderNotifications,
  ProductArtwork,
  RevenueChart,
  SiteBlockRenderer,
  StaffSelect,
  StatePanel,
  StatusPill,
  StorefrontFrame,
  StorefrontHeader,
  StorefrontPage,
  ThreeScene,
  CartDrawer,
  ProductCard,
  ProductViewer,
  CollectionEditor,
}

export default defineNuxtPlugin((nuxtApp) => {
  for (const [name, component] of Object.entries(components)) {
    nuxtApp.vueApp.component(name, component)
  }
})
