// Deterministic RNG. Every career is reproducible from its seed, which is what
// makes the sim harness and the game the same system.

export class RNG {
  constructor(seed = 1) {
    this.s = (seed >>> 0) || 1;
    this._spare = null;
  }

  // mulberry32
  next() {
    this.s = (this.s + 0x6d2b79f5) >>> 0;
    let t = this.s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  float(a = 0, b = 1) {
    return a + (b - a) * this.next();
  }

  int(a, b) {
    return Math.floor(this.float(a, b + 1));
  }

  // Box-Muller, one cached spare.
  gauss(mu = 0, sd = 1) {
    if (this._spare !== null) {
      const v = this._spare;
      this._spare = null;
      return mu + sd * v;
    }
    let u = 0, v = 0, s = 0;
    do {
      u = this.float(-1, 1);
      v = this.float(-1, 1);
      s = u * u + v * v;
    } while (s === 0 || s >= 1);
    const f = Math.sqrt((-2 * Math.log(s)) / s);
    this._spare = v * f;
    return mu + sd * u * f;
  }

  chance(p) {
    return this.next() < p;
  }

  pick(arr) {
    return arr[Math.floor(this.next() * arr.length)];
  }

  weighted(entries) {
    // entries: [[value, weight], ...]
    let total = 0;
    for (const [, w] of entries) total += w;
    let r = this.next() * total;
    for (const [v, w] of entries) {
      r -= w;
      if (r <= 0) return v;
    }
    return entries[entries.length - 1][0];
  }

  shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(this.next() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
}

export const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
export const sig = (x) => 1 / (1 + Math.exp(-x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const mean = (xs) => xs.reduce((a, b) => a + b, 0) / (xs.length || 1);
export const median = (xs) => {
  const s = xs.slice().sort((a, b) => a - b);
  if (!s.length) return 0;
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
export const quantile = (xs, p) => {
  const s = xs.slice().sort((a, b) => a - b);
  if (!s.length) return 0;
  return s[clamp(Math.floor(p * s.length), 0, s.length - 1)];
};
