const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const API_KEY_STORAGE = "tradingagents_api_key";

export function getStoredApiKey() {
  return localStorage.getItem(API_KEY_STORAGE) || "";
}

export function setStoredApiKey(value) {
  const key = value.trim();
  if (key) {
    localStorage.setItem(API_KEY_STORAGE, key);
  } else {
    localStorage.removeItem(API_KEY_STORAGE);
  }
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const apiKey = getStoredApiKey();

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (apiKey) {
    headers.set("X-API-Key", apiKey);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  let payload = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { detail: text };
    }
  }

  if (!response.ok) {
    const message = payload?.detail || `Request failed with ${response.status}`;
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg).join("; ") : message);
  }

  return payload;
}

export function getHealth() {
  return fetch("/health").then((response) => response.json());
}

