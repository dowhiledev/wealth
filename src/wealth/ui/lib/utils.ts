import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatAmount(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-"
  const num = Number(value)
  if (!isFinite(num)) return String(value)
  const abs = Math.abs(num)
  const maximumFractionDigits = abs > 1 ? 2 : 5
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(num)
}
