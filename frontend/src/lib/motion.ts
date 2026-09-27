export const ease = {
  out:    [0.16, 1, 0.3, 1],     // expo out: default for entrances
  quart:  [0.25, 1, 0.5, 1],     // UI state changes
  inOut:  [0.87, 0, 0.13, 1],    // page and section transitions
  stamp:  [0.34, 1.56, 0.64, 1], // slight overshoot: verdict stamp only
} as const;

export const dur = { micro: 0.16, ui: 0.32, reveal: 0.8, story: 1.2 } as const;
export const stagger = { words: 0.06, lines: 0.09, cards: 0.07 } as const;
