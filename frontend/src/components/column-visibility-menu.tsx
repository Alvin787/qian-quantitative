import { Columns3 } from "lucide-react"
import { Popover } from "@base-ui/react/popover"

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
  return (
    <Popover.Root>
      <Popover.Trigger
        disabled={columns.length === 0}
        render={<Button type="button" variant="outline" size="sm" />}
      >
        <Columns3 aria-hidden />
        Columns
        <span className="text-muted-foreground tabular-nums">
          {visibleColumns.length}/{columns.length}
        </span>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Positioner
          side="bottom"
          align="end"
          sideOffset={6}
          collisionPadding={8}
        >
          <Popover.Popup className="surface-enter bg-popover text-popover-foreground border-border z-50 max-h-80 w-64 overflow-y-auto rounded-lg border p-2 shadow-lg backdrop-blur-xl">
            <div className="flex items-center justify-between px-1 pb-2">
              <Popover.Title className="text-muted-foreground text-xs font-medium tracking-wide">
                Visible columns
              </Popover.Title>
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
                  <label className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-md px-1.5 py-1.5 text-sm">
                    <input
                      type="checkbox"
                      className="accent-primary size-3.5"
                      checked={visibleColumns.includes(column)}
                      onChange={(event) =>
                        onToggle(column, event.target.checked)
                      }
                    />
                    <span className="truncate">{columnLabel(column)}</span>
                  </label>
                </li>
              ))}
            </ul>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  )
}
