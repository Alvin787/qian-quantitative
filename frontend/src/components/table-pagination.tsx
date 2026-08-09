import type { JSX } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"

export function TablePagination({
  page,
  pageCount,
  totalRows,
  pageSize,
  onPageChange,
}: {
  page: number
  pageCount: number
  totalRows: number
  pageSize: number
  onPageChange: (page: number) => void
}): JSX.Element | null {
  if (pageCount <= 1) return null

  const rangeStart = (page - 1) * pageSize + 1
  const rangeEnd = Math.min(page * pageSize, totalRows)

  return (
    <nav
      aria-label="Results pagination"
      className="flex flex-wrap items-center justify-between gap-2 px-1 py-2"
    >
      <span className="text-muted-foreground text-sm">
        Showing {rangeStart}–{rangeEnd} of {totalRows}
      </span>
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label="Previous page"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft aria-hidden />
        </Button>
        <span className="text-sm tabular-nums">
          Page {page} of {pageCount}
        </span>
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label="Next page"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight aria-hidden />
        </Button>
      </div>
    </nav>
  )
}
