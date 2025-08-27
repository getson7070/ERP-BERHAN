if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/sw.js');
  });
}

async function queueAction(action) {
  if (!('serviceWorker' in navigator)) return;
  const reg = await navigator.serviceWorker.ready;
  reg.active?.postMessage({ type: 'QUEUE_ACTION', payload: action });
  if ('sync' in reg) {
    try { await reg.sync.register('flush-actions'); } catch (e) { /* ignore */ }
  }
}

window.addEventListener('online', () => {
  navigator.serviceWorker.ready.then(reg => {
    if ('sync' in reg) {
      reg.sync.register('flush-actions');
    }
  });
});

window.queueAction = queueAction;
