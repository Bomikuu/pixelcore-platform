let googleScriptPromise

function loadGoogleIdentity() {
  if (!import.meta.client) return Promise.reject(new Error('Google sign-in is only available in the browser.'))
  if (window.google?.accounts?.id) return Promise.resolve(window.google)
  if (!googleScriptPromise) {
    googleScriptPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-pixelcore-google-identity]')
      if (existing) {
        existing.addEventListener('load', () => resolve(window.google), { once: true })
        existing.addEventListener('error', () => reject(new Error('Google sign-in could not load.')), { once: true })
        return
      }
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.defer = true
      script.dataset.pixelcoreGoogleIdentity = 'true'
      script.onload = () => resolve(window.google)
      script.onerror = () => reject(new Error('Google sign-in could not load.'))
      document.head.appendChild(script)
    })
  }
  return googleScriptPromise
}

export function useGoogleIdentity() {
  const config = useRuntimeConfig()

  async function requestCredential() {
    const clientId = config.public.googleIdentityClientId
    if (!clientId) throw new Error('Google sign-in is not configured for this environment.')
    const google = await loadGoogleIdentity()
    return new Promise((resolve, reject) => {
      let settled = false
      google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          settled = true
          response?.credential ? resolve(response.credential) : reject(new Error('Google did not return a credential.'))
        },
      })
      google.accounts.id.prompt((notification) => {
        if (!settled && (notification.isNotDisplayed?.() || notification.isSkippedMoment?.())) {
          reject(new Error('Google sign-in was closed or unavailable.'))
        }
      })
    })
  }

  return { requestCredential }
}
