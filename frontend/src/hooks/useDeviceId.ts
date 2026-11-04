import { useState } from "react";

const KEY = "cb.deviceId";

/** randomUUID only exists in secure contexts (https/localhost); plain http://<LAN-IP> needs the fallback. */
export function newId(): string {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

/** Stable per-device id kept in localStorage (falls back to a per-call id if storage is blocked). */
export function getDeviceId(): string {
  try {
    const existing = localStorage.getItem(KEY);
    if (existing) return existing;
    const id = newId();
    localStorage.setItem(KEY, id);
    return id;
  } catch {
    return newId();
  }
}

export function useDeviceId(): string {
  const [id] = useState(getDeviceId);
  return id;
}
