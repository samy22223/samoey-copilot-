import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
 
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(input: string | number | Date): string {
  const date = new Date(input)
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  })
}

export function absoluteUrl(path: string) {
  return `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}${path}`
}

export function formatBytes(
  bytes: number,
  opts: {
    decimals?: number
    sizeType?: "decimal" | "binary"
  } = {}) {
  const { decimals = 0, sizeType = "decimal" } = opts
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"]
  const k = sizeType === "decimal" ? 1000 : 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`
}

export function formatTimeAgo(date: Date): string {
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  const minute = 60
  const hour = minute * 60
  const day = hour * 24
  const month = day * 30
  const year = day * 365
  
  if (diffInSeconds < minute) {
    return 'just now'
  } else if (diffInSeconds < hour) {
    const minutes = Math.floor(diffInSeconds / minute)
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  } else if (diffInSeconds < day) {
    const hours = Math.floor(diffInSeconds / hour)
    return `${hours} hour${hours > 1 ? 's' : ''} ago`
  } else if (diffInSeconds < month) {
    const days = Math.floor(diffInSeconds / day)
    return `${days} day${days > 1 ? 's' : ''} ago`
  } else if (diffInSeconds < year) {
    const months = Math.floor(diffInSeconds / month)
    return `${months} month${months > 1 ? 's' : ''} ago`
  } else {
    const years = Math.floor(diffInSeconds / year)
    return `${years} year${years > 1 ? 's' : ''} ago`
  }
}
