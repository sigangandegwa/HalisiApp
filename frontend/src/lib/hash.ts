/**
 * Perceptual-hash helpers for the 8x8 bit grids (FRONTEND.md section 7, hash-grid).
 * The API sends 64-bit hashes as 16 lowercase hex characters (imagehash's `str(phash)` format:
 * the 8x8 boolean matrix flattened row-major, most significant bit first).
 */

export function isHash(hex: string | null | undefined): hex is string {
  return typeof hex === "string" && /^[0-9a-f]{16}$/i.test(hex);
}

/** 16 hex chars -> 64 booleans, row-major. */
export function hexToBits(hex: string): boolean[] {
  const bits: boolean[] = [];
  for (const ch of hex.toLowerCase()) {
    const n = parseInt(ch, 16);
    for (let i = 3; i >= 0; i--) bits.push(((n >> i) & 1) === 1);
  }
  return bits;
}

/** Indices where two hashes differ. */
export function diffBits(a: string, b: string): Set<number> {
  const x = hexToBits(a);
  const y = hexToBits(b);
  const out = new Set<number>();
  for (let i = 0; i < 64; i++) if (x[i] !== y[i]) out.add(i);
  return out;
}

export function hamming(a: string, b: string): number {
  return diffBits(a, b).size;
}

/**
 * Browser-side pHash preview for onboarding (same algorithm family as imagehash.phash: 32x32
 * greyscale, 2-D DCT, top-left 8x8 without the DC term, compared with the median). The engine's
 * value is authoritative; this is only shown, labelled, while the engine is offline.
 */
export async function previewPhash(file: Blob): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const size = 32;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Canvas unavailable");
  ctx.fillStyle = "#ffffff"; // transparent logos are composited on white, like the engine
  ctx.fillRect(0, 0, size, size);
  const side = Math.max(bitmap.width, bitmap.height);
  const scale = size / side;
  const w = bitmap.width * scale;
  const h = bitmap.height * scale;
  ctx.drawImage(bitmap, (size - w) / 2, (size - h) / 2, w, h);
  const { data } = ctx.getImageData(0, 0, size, size);
  const grey = new Float64Array(size * size);
  for (let i = 0; i < size * size; i++) {
    grey[i] = 0.299 * data[i * 4] + 0.587 * data[i * 4 + 1] + 0.114 * data[i * 4 + 2];
  }
  const dct1 = (input: Float64Array, stride: number, offset: number, out: Float64Array) => {
    for (let k = 0; k < size; k++) {
      let sum = 0;
      for (let n = 0; n < size; n++) sum += input[offset + n * stride] * Math.cos((Math.PI * (2 * n + 1) * k) / (2 * size));
      out[k] = sum;
    }
  };
  const rows = new Float64Array(size * size);
  const tmp = new Float64Array(size);
  for (let r = 0; r < size; r++) {
    dct1(grey, 1, r * size, tmp);
    rows.set(tmp, r * size);
  }
  const coeffs = new Float64Array(size * size);
  for (let c = 0; c < size; c++) {
    dct1(rows, size, c, tmp);
    for (let r = 0; r < size; r++) coeffs[r * size + c] = tmp[r];
  }
  const low: number[] = [];
  for (let r = 0; r < 8; r++) for (let c = 0; c < 8; c++) low.push(coeffs[r * size + c]);
  const median = [...low.slice(1)].sort((a, b) => a - b)[31];
  let hex = "";
  for (let i = 0; i < 64; i += 4) {
    let nibble = 0;
    for (let j = 0; j < 4; j++) nibble = (nibble << 1) | (low[i + j] > median ? 1 : 0);
    hex += nibble.toString(16);
  }
  bitmap.close();
  return hex;
}
