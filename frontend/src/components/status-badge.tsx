import type { StatusTone } from "@/lib/screener-columns"
import { cn } from "@/lib/utils"

export type { StatusTone }

const TONE_CLASS: Record<StatusTone, string> = {
  positive:
    "bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  negative:
    "bg-red-500/15 text-red-700 dark:bg-red-500/20 dark:text-red-300",
  neutral: "bg-muted text-muted-foreground",
}

export function StatusBadge({
  tone,
  label,
  className,
}: {
  tone: StatusTone
  label: string
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        TONE_CLASS[tone],
        className
      )}
    >
      {label}
    </span>
  )
}
