import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react"

import { StatusBadge } from "@/components/status-badge"
import { DelimitedPills, decodeDisplayText } from "@/components/token-pills"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ResultRow } from "@/lib/screener-api"
import {
  columnDescription,
  columnLabel,
  formatValue,
  statusBadgeFor,
} from "@/lib/screener-columns"
import { tradingViewUrl } from "@/lib/tradingview"
import { cn } from "@/lib/utils"

const DELIMITED_COLUMNS = new Set(["fail_reasons", "warnings", "source_screens"])
const LEFT_ALIGNED_COLUMNS = new Set([
  "ticker",
  "fail_reasons",
  "warnings",
  "source_screens",
  "industry",
])

function rowTradingViewUrl(row: ResultRow) {
  return tradingViewUrl(
    String(row.ticker ?? row.symbol ?? ""),
    String(row.exchange ?? "")
  )
}

export function ScreenerResultsTable({
  columns,
  rows,
  emptyMessage = "No rows match the current filters.",
  sortColumn,
  sortDirection,
  onToggleSort,
}: {
  columns: string[]
  rows: ResultRow[]
  emptyMessage?: string
  sortColumn: string | null
  sortDirection: "asc" | "desc"
  onToggleSort: (column: string) => void
}) {
  if (columns.length === 0) {
    return (
      <p className="text-muted-foreground p-6 text-sm">
        No columns are visible. Enable at least one column.
      </p>
    )
  }

  return (
    <TooltipProvider>
      <Table className="w-max min-w-full text-xs sm:text-sm">
        <TableHeader className="bg-muted/50 sticky top-0 z-10">
          <TableRow>
            {columns.map((column) => {
              const active = column === sortColumn
              const description = columnDescription(column)
              const centered = !LEFT_ALIGNED_COLUMNS.has(column)
              const sortButton = (
                <button
                  type="button"
                  onClick={() => onToggleSort(column)}
                  className={cn(
                    "focus-visible:ring-ring flex w-full items-center gap-0.5 px-2 py-1.5 text-left font-medium outline-none focus-visible:ring-2",
                    centered && "justify-center text-center",
                    active && "text-foreground"
                  )}
                >
                  <span
                    className={cn(
                      description &&
                        "decoration-muted-foreground/60 underline decoration-dotted underline-offset-4"
                    )}
                  >
                    {columnLabel(column)}
                  </span>
                  {active ? (
                    sortDirection === "asc" ? (
                      <ArrowUp className="size-3" aria-hidden />
                    ) : (
                      <ArrowDown className="size-3" aria-hidden />
                    )
                  ) : (
                    <ChevronsUpDown className="size-3 opacity-40" aria-hidden />
                  )}
                </button>
              )

              return (
                <TableHead
                  key={column}
                  scope="col"
                  aria-sort={
                    active
                      ? sortDirection === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                  className={cn(
                    "h-9 whitespace-nowrap p-0",
                    centered && "text-center"
                  )}
                >
                  {description ? (
                    <Tooltip>
                      <TooltipTrigger asChild>{sortButton}</TooltipTrigger>
                      <TooltipContent side="top">{description}</TooltipContent>
                    </Tooltip>
                  ) : (
                    sortButton
                  )}
                </TableHead>
              )
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length}
                className="text-muted-foreground h-24 text-center"
              >
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row, index) => (
              <TableRow key={String(row.ticker ?? index)}>
                {columns.map((column) => {
                  const value = row[column]
                  const badge = statusBadgeFor(value ?? null, column)
                  const isDelimited = DELIMITED_COLUMNS.has(column)
                  const centered = !LEFT_ALIGNED_COLUMNS.has(column)
                  const tickerUrl =
                    column === "ticker" ? rowTradingViewUrl(row) : null
                  return (
                    <TableCell
                      key={column}
                      className={cn(
                        "max-w-[16rem] truncate px-2 py-1.5",
                        isDelimited && "max-w-sm whitespace-normal",
                        centered && "text-center",
                        typeof value === "number" && "tabular-nums",
                        column === "ticker" && "font-medium"
                      )}
                      title={
                        !badge &&
                        !isDelimited &&
                        typeof value === "string" &&
                        value
                          ? value
                          : undefined
                      }
                    >
                      {isDelimited && typeof value === "string" ? (
                        <DelimitedPills
                          value={value}
                          variant={
                            column === "warnings"
                              ? "warning"
                              : column === "source_screens"
                                ? "neutral"
                                : "failure"
                          }
                        />
                      ) : tickerUrl ? (
                        <a
                          href={tickerUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-foreground underline decoration-muted-foreground/50 underline-offset-2 hover:decoration-foreground"
                          title={`Open ${String(value)} on TradingView`}
                        >
                          {formatValue(value ?? null)}
                        </a>
                      ) : badge ? (
                        <StatusBadge tone={badge.tone} label={badge.label} />
                      ) : column === "industry" && typeof value === "string" ? (
                        decodeDisplayText(value)
                      ) : (
                        formatValue(value ?? null)
                      )}
                    </TableCell>
                  )
                })}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TooltipProvider>
  )
}
