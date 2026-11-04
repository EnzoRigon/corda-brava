// Chiptune SFX synthesised with Web Audio; no audio files. Every call is a silent no-op when muted,
// when AudioContext is missing, or while the context is suspended (autoplay policy).
export type SfxName = "click" | "tap" | "join" | "countdown" | "whistle" | "swing" | "heartbeat" | "win" | "draw";

const MUTE_KEY = "cb.muted";
const MASTER = 0.18;

function readMuted(): boolean {
  try {
    return localStorage.getItem(MUTE_KEY) === "1";
  } catch {
    return false;
  }
}

let muted = readMuted();
let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let noiseBuf: AudioBuffer | null = null;
const listeners = new Set<() => void>();

export const isMuted = () => muted;
export const subscribe = (fn: () => void) => (listeners.add(fn), () => void listeners.delete(fn));
export function setMuted(v: boolean) {
  muted = v;
  try {
    localStorage.setItem(MUTE_KEY, v ? "1" : "0");
  } catch {
    // storage blocked: mute lasts for this page load only
  }
  listeners.forEach((l) => l());
}

/** Create the context lazily inside a user gesture and resume it. */
export function unlock() {
  try {
    const AC = typeof window !== "undefined" ? (window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext) : undefined;
    if (!AC) return;
    if (!ctx) {
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = MASTER;
      master.connect(ctx.destination);
    }
    if (ctx.state === "suspended") void ctx.resume();
  } catch {
    ctx = null;
  }
}
if (typeof window !== "undefined") {
  window.addEventListener("pointerdown", unlock, { passive: true });
  window.addEventListener("keydown", unlock);
}

interface Tone { type?: OscillatorType; f: number; to?: number; at?: number; d: number; v?: number }

function tone(c: AudioContext, { type = "square", f, to, at = 0, d, v = 0.5 }: Tone) {
  const t = c.currentTime + at;
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = type;
  o.frequency.setValueAtTime(f, t);
  if (to) o.frequency.exponentialRampToValueAtTime(to, t + d);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(v, t + 0.005);
  g.gain.exponentialRampToValueAtTime(0.0001, t + d);
  o.connect(g).connect(master!);
  o.start(t);
  o.stop(t + d + 0.02);
}

function noise(c: AudioContext, at: number, d: number, v: number, from: number, to: number) {
  noiseBuf ??= (() => {
    const b = c.createBuffer(1, c.sampleRate, c.sampleRate);
    const a = b.getChannelData(0);
    for (let i = 0; i < a.length; i++) a[i] = Math.random() * 2 - 1;
    return b;
  })();
  const t = c.currentTime + at;
  const s = c.createBufferSource();
  s.buffer = noiseBuf;
  const fl = c.createBiquadFilter();
  fl.type = "bandpass";
  fl.frequency.setValueAtTime(from, t);
  fl.frequency.exponentialRampToValueAtTime(to, t + d);
  const g = c.createGain();
  g.gain.setValueAtTime(v, t);
  g.gain.exponentialRampToValueAtTime(0.0001, t + d);
  s.connect(fl).connect(g).connect(master!);
  s.start(t);
  s.stop(t + d + 0.02);
}

const arp = (notes: number[], step: number, type: OscillatorType = "square"): Tone[] =>
  notes.map((f, i) => ({ type, f, at: i * step, d: step * 1.6, v: 0.4 }));

const RECIPES: Record<SfxName, (c: AudioContext) => void> = {
  click: (c) => tone(c, { f: 880, to: 520, d: 0.05, v: 0.35 }),
  tap: (c) => tone(c, { type: "triangle", f: 500, to: 900, d: 0.06, v: 0.6 }),
  join: (c) => arp([660, 990], 0.08).forEach((t) => tone(c, t)),
  countdown: (c) => tone(c, { f: 440, d: 0.14, v: 0.45 }),
  whistle: (c) => {
    tone(c, { type: "triangle", f: 2300, to: 2500, d: 0.35, v: 0.5 });
    tone(c, { type: "triangle", f: 2380, to: 2560, at: 0.02, d: 0.33, v: 0.4 });
    noise(c, 0, 0.35, 0.15, 3000, 4000);
  },
  swing: (c) => noise(c, 0, 0.18, 0.5, 400, 2200),
  heartbeat: (c) => {
    tone(c, { type: "triangle", f: 70, to: 45, d: 0.12, v: 0.9 });
    tone(c, { type: "triangle", f: 60, to: 40, at: 0.17, d: 0.14, v: 0.7 });
  },
  win: (c) => [...arp([523, 659, 784, 1047], 0.1), { type: "square", f: 1047, at: 0.4, d: 0.5, v: 0.4 } as Tone].forEach((t) => tone(c, t)),
  draw: (c) => arp([392, 392, 330], 0.16, "triangle").forEach((t) => tone(c, t)),
};

export function play(name: SfxName) {
  if (muted || !ctx || !master || ctx.state !== "running") return;
  try {
    RECIPES[name](ctx);
  } catch {
    // audio must never break the game
  }
}
