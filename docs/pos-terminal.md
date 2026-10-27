# POS counter

Open `/pos-terminal` and pair the device using its eight-character setup code from
Sell → POS. The active counter keeps the catalog, current order, and payment actions
within the same workspace. Grid/list preference is saved on this device. Quick items
filters the favorites configured for this station.

## Barcode readers

USB and Bluetooth readers must act as a keyboard and send Enter after the code.
Readers work in product search and, while the unobstructed sale catalog is active,
without focusing the search field. Normal typing in payment, customer, note, or other
dialog fields is left alone. A reader configured with unusually slow per-character
delays should use the search field.

Lookup matches the product SKU or `metadata.barcode`, and active variant SKU/barcode.
Leading zeroes remain part of the code. A unique variant code selects that variant.
Required options still need confirmation. Unknown or duplicate codes show a message
and leave the order unchanged; the catalog includes variant codes in search results.
Typing an exact unique product name and pressing Enter also opens or adds that item.

## Camera scanner

Use the scanner button in search, or F4, to open the camera. Allow camera access when
the browser asks. The scanner uses the rear-facing camera when available and closes
after decoding one barcode or QR code. Entering a code manually is always available.

The camera feed is decoded locally using the lazily loaded
[ZXing browser library](https://github.com/zxing-js/browser). Camera frames are not sent
to the POS API. Tracks stop when scanning completes, the dialog closes, the page is
hidden, or the counter is left. A camera paused by hiding the page requires Retry camera.

Camera access needs [HTTPS or localhost and browser permission](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).
Denied, unavailable, and busy cameras display a recovery message while retaining manual
entry and connected-reader support.

## Shortcuts

| Shortcut | Action |
| --- | --- |
| F2 or Ctrl/Cmd K | Focus product search |
| F4 | Open the camera/code scanner |
| F8 | Open payment for the current order |
| Ctrl/Cmd Shift H | Hold the current order |

Shortcuts are inactive while a dialog or menu is open. The register controls menu also
lists them. Save order uses the existing held-sale flow; Receipts opens recent completed
transactions for reprinting or emailing. The counter cannot change its own strict-mode
configuration or bypass manager approval.

## Cart behavior

Repeated additions increase quantity only when product, variant, options, and empty
item note match. Annotated lines remain separate. Prices, taxes, discounts, and totals
continue to come from the backend. Rejected updates restore the last confirmed order.
An offline counter blocks additions and payment rather than presenting an unconfirmed sale.
