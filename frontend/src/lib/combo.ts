/** Combo meter: m in [0,1]. Each tap adds GAIN, time drains DECAY_PER_S, so ~4 taps/s holds the bar steady. */
export const COMBO_GAIN = 0.1;
export const COMBO_DECAY_PER_S = 0.4;
export const COMBO_MIN_SHOWN = 0.15;

export const tapCombo = (m: number) => Math.min(1, m + COMBO_GAIN);
export const decayCombo = (m: number, dtMs: number) => Math.max(0, m - (COMBO_DECAY_PER_S * dtMs) / 1000);
/** 0 = no combo shown, otherwise 1..10. */
export const comboLevel = (m: number) => (m < COMBO_MIN_SHOWN ? 0 : 1 + Math.floor(m * 9));
