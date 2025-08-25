if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/sw.js');
  });
}

const DB_NAME = 'erp-offline';
const STORE = 'actions';

function dbPromise() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE, { autoIncrement: true });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function queueAction(action) {
  const db = await dbPromise();
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).add(action);
  return tx.complete;
}

async function flushActions() {
  const db = await dbPromise();
  const tx = db.transaction(STORE, 'readwrite');
  const store = tx.objectStore(STORE);
  const all = store.getAll();
  all.onsuccess = async () => {
    const items = all.result || [];
    for (const item of items) {
      try {
        await fetch(item.url, item.options);
      } catch (e) {
        console.error('sync failed', e);
        return;
      }
    }
    store.clear();
  };
}

window.addEventListener('online', flushActions);
window.queueAction = queueAction;
