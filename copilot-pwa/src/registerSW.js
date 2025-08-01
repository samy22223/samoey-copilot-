import { Workbox } from 'workbox-window'

const registerSW = () => {
  if ('serviceWorker' in navigator) {
    const wb = new Workbox('/sw.js')
    wb.register()
      .then(() => console.log('Service Worker registered'))
      .catch(err => console.error('Service Worker registration failed', err))
  }
}

export default registerSW
