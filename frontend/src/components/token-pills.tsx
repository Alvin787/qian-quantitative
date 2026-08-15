import { cn } from "@/lib/utils"

export type PillVariant = "failure" | "warning" | "neutral"

const VARIANT_CLASS: Record<PillVariant, string> = {
  failure: "bg-red-500/15 text-red-700 dark:bg-red-500/20 dark:text-red-300",
  warning:
    "bg-amber-500/15 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
  neutral: "bg-muted text-muted-foreground",
}

export function decodeDisplayText(value: string) {
  return value
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
}

export function TokenPills({
  items,
  variant,
  labelFor,
  titleFor,
}: {
  items: readonly string[]
  variant: PillVariant
  labelFor?: (item: string) => string
  titleFor?: (item: string) => string
}) {
  const cleaned = items.map((item) => item.trim()).filter(Boolean)

  if (cleaned.length === 0) {
    return <span className="text-muted-foreground">—</span>
  }

  return (
    <div
      className={cn(
        "flex gap-1",
        variant === "warning"
          ? "max-w-[20rem] flex-nowrap overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          : "flex-wrap"
      )}
    >
      {cleaned.map((item, index) => (
        <span
          key={`${item}-${index}`}
          title={titleFor?.(item)}
          className={cn(
            "inline-flex rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap",
            VARIANT_CLASS[variant]
          )}
        >
          {decodeDisplayText(labelFor ? labelFor(item) : item)}
        </span>
      ))}
    </div>
  )
}

export function DelimitedPills({
  value,
  variant,
  labelFor,
  titleFor,
}: {
  value: string
  variant: PillVariant
  labelFor?: (item: string) => string
  titleFor?: (item: string) => string
}) {
  return (
    <TokenPills
      items={value.split(";")}
      variant={variant}
      labelFor={labelFor}
      titleFor={titleFor}
    />
  )
}
