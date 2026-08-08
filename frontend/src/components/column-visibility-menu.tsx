import { useEffect, useId, useRef, useState } from "react"
import { Columns3 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { columnLabel } from "@/lib/screener-columns"

export function ColumnVisibilityMenu({
  columns,
  visibleColumns,
  onToggle,
  onReset,
}: {
  columns: string[]
  visibleColumns: string[]
  onToggle: (column: string, visible: boolean) => void
  onReset: () => void
}) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const menuId = useId()

  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false)
    }

    document.addEventListener("pointerdown", onPointerDown)
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("pointerdown", onPointerDown)
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open])

  return (
    <div ref={containerRef} className="relative">
      <Button
        type="button"
        variant="outline"
        size="sm"
        aria-expanded={open}
        aria-controls={menuId}
        aria-haspopup="true"
        disabled={columns.length === 0}
        onClick={() => setOpen((value) => !value)}
      >
        <Columns3 aria-hidden />
        Columns
        <span className="text-muted-foreground tabular-nums">
          {visibleColumns.length}/{columns.length}
        </span>
      </Button>

      {open ? (
        <div
          id={menuId}
          className="bg-popover text-popover-foreground border-border absolute right-0 z-20 mt-1 max-h-80 w-64 overflow-y-auto rounded-md border p-2 shadow-md"
        >
          <div className="flex items-center justify-between px-1 pb-2">
            <span className="text-muted-foreground text-xs font-medium">
              Visible columns
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={onReset}
            >
              Reset
            </Button>
          </div>
          <ul className="flex flex-col">
            {columns.map((column) => (
              <li key={column}>
                <label className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded px-1 py-1 text-sm">
                  <input
                    type="checkbox"
                    className="accent-primary size-3.5"
                    checked={visibleColumns.includes(column)}
                    onChange={(event) => onToggle(column, event.target.checked)}
                  />
                  <span className="truncate">{columnLabel(column)}</span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
