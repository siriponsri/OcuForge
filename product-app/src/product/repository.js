const DB_NAME = "ocuforge-product-poc";
const DB_VERSION = 1;
const STATE_KEY = "workspace";
const FALLBACK_KEY = "ocuforge-product-poc-v2";

function hasIndexedDb() {
  return typeof indexedDB !== "undefined";
}

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      request.result.createObjectStore("documents");
      request.result.createObjectStore("objects");
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function transaction(db, storeName, mode, action) {
  return new Promise((resolve, reject) => {
    const request = action(db.transaction(storeName, mode).objectStore(storeName));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export class CaseRepository {
  async loadState(fallbackState) {
    if (!hasIndexedDb()) {
      try {
        return JSON.parse(localStorage.getItem(FALLBACK_KEY)) || fallbackState;
      } catch {
        return fallbackState;
      }
    }
    try {
      const db = await openDb();
      const state = await transaction(db, "documents", "readonly", (store) => store.get(STATE_KEY));
      return state || fallbackState;
    } catch {
      return fallbackState;
    }
  }

  async saveState(state) {
    if (!hasIndexedDb()) {
      localStorage.setItem(FALLBACK_KEY, JSON.stringify(state));
      return;
    }
    const db = await openDb();
    await transaction(db, "documents", "readwrite", (store) => store.put(state, STATE_KEY));
  }

  async putObject(key, value) {
    if (!hasIndexedDb()) return;
    const db = await openDb();
    const existing = await transaction(db, "objects", "readonly", (store) => store.get(key));
    if (existing) return;
    await transaction(db, "objects", "readwrite", (store) => store.put(value, key));
  }

  async getObject(key) {
    if (!hasIndexedDb()) return null;
    const db = await openDb();
    return transaction(db, "objects", "readonly", (store) => store.get(key));
  }

  async clear() {
    if (!hasIndexedDb()) {
      localStorage.removeItem(FALLBACK_KEY);
      return;
    }
    const db = await openDb();
    await Promise.all([transaction(db, "documents", "readwrite", (store) => store.clear()), transaction(db, "objects", "readwrite", (store) => store.clear())]);
  }
}

export const caseRepository = new CaseRepository();
