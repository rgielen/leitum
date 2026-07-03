// Number of characters that should be visible at `frame` when typing `total`
// characters starting at `start`, at `cps` characters per second.
export const typedCount = (
  frame: number,
  start: number,
  total: number,
  fps: number,
  cps: number,
): number => {
  const elapsed = (frame - start) / fps;
  if (elapsed <= 0) return 0;
  return Math.min(total, Math.floor(elapsed * cps));
};
