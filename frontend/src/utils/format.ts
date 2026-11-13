export function discountPercent(price: number, discount?: number | null) {
  if (!discount || discount >= price) return null;
  return Math.round(((price - discount) / price) * 100);
}
