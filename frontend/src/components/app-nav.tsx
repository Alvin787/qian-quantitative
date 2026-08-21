import { useId, useState } from "react"
import { Dialog } from "@base-ui/react/dialog"
import {
  BookOpen,
  ChevronDown,
  CircleDollarSign,
  ListFilter,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Scale,
  ScanSearch,
  X,
} from "lucide-react"

import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import type { Strategy } from "@/lib/screener-api"
import { usePersistentState } from "@/lib/use-persistent-state"
import { cn } from "@/lib/utils"

const SIDEBAR_STORAGE_KEY = "qq.sidebar.collapsed"

export type AppTab = "screener" | "diary" | "positions" | "pnl" | "watchlists"

function ScreenerNav({
  strategies,
  selectedStrategyId,
  onSelectStrategy,
  strategyHighlight,
  collapsed = false,
  expanded,
  listId,
  onToggleExpanded,
  onExpandSidebar,
  onNavigate,
}: {
  strategies: Strategy[]
  selectedStrategyId: string | null
  onSelectStrategy: (strategyId: string) => void
  strategyHighlight: boolean
  collapsed?: boolean
  expanded: boolean
  listId: string
  onToggleExpanded: () => void
  onExpandSidebar?: () => void
  onNavigate?: () => void
}) {
  return (
    <div>
      <button
        type="button"
        aria-expanded={collapsed ? false : expanded}
        aria-controls={collapsed ? undefined : listId}
        title={collapsed ? "Screener" : undefined}
        onClick={() => {
          if (collapsed) {
            onExpandSidebar?.()
          } else {
            onToggleExpanded()
          }
        }}
        className={cn(
          "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
          "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
          "active:scale-[0.98]",
          "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
          collapsed && "justify-center px-0",
          "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        )}
      >
        <ScanSearch className="size-4 shrink-0" aria-hidden />
        <span className={cn("flex-1 text-left", collapsed && "sr-only")}>
          Screener
        </span>
        {!collapsed ? (
          <ChevronDown
            className={cn(
              "size-4 shrink-0 opacity-70 transition-transform duration-200 ease-[var(--ease-out)]",
              !expanded && "-rotate-90"
            )}
            aria-hidden
          />
        ) : null}
      </button>
      {!collapsed && expanded ? (
        <ul id={listId} className="mt-1 flex flex-col gap-0.5 pl-2">
          {strategies.map((strategy) => {
            const current =
              strategyHighlight && strategy.id === selectedStrategyId
            return (
              <li key={strategy.id}>
                <button
                  type="button"
                  aria-current={current ? "page" : undefined}
                  onClick={() => {
                    onSelectStrategy(strategy.id)
                    onNavigate?.()
                  }}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium",
                    "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
                    "active:scale-[0.98]",
                    "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
                    current
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  )}
                >
                  {strategy.label}
                </button>
              </li>
            )
          })}
        </ul>
      ) : null}
    </div>
  )
}

function WatchlistsNavButton({
  active,
  collapsed = false,
  onSelect,
  onExpandSidebar,
  onNavigate,
}: {
  active: boolean
  collapsed?: boolean
  onSelect: () => void
  onExpandSidebar?: () => void
  onNavigate?: () => void
}) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      title={collapsed ? "Watchlists" : undefined}
      onClick={() => {
        if (collapsed) {
          onExpandSidebar?.()
        }
        onSelect()
        onNavigate?.()
      }}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
        "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
        "active:scale-[0.98]",
        "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
        collapsed && "justify-center px-0",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      )}
    >
      <ListFilter className="size-4 shrink-0" aria-hidden />
      <span className={cn(collapsed && "sr-only")}>Watchlists</span>
    </button>
  )
}

function DiaryNavButton({
  active,
  collapsed = false,
  onSelect,
  onExpandSidebar,
  onNavigate,
}: {
  active: boolean
  collapsed?: boolean
  onSelect: () => void
  onExpandSidebar?: () => void
  onNavigate?: () => void
}) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      title={collapsed ? "Market Diary" : undefined}
      onClick={() => {
        if (collapsed) {
          onExpandSidebar?.()
        }
        onSelect()
        onNavigate?.()
      }}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
        "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
        "active:scale-[0.98]",
        "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
        collapsed && "justify-center px-0",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      )}
    >
      <BookOpen className="size-4 shrink-0" aria-hidden />
      <span className={cn(collapsed && "sr-only")}>Market Diary</span>
    </button>
  )
}

function PositionsNavButton({
  active,
  collapsed = false,
  onSelect,
  onExpandSidebar,
  onNavigate,
}: {
  active: boolean
  collapsed?: boolean
  onSelect: () => void
  onExpandSidebar?: () => void
  onNavigate?: () => void
}) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      title={collapsed ? "Positions" : undefined}
      onClick={() => {
        if (collapsed) {
          onExpandSidebar?.()
        }
        onSelect()
        onNavigate?.()
      }}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
        "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
        "active:scale-[0.98]",
        "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
        collapsed && "justify-center px-0",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      )}
    >
      <Scale className="size-4 shrink-0" aria-hidden />
      <span className={cn(collapsed && "sr-only")}>Positions</span>
    </button>
  )
}

function PnlNavButton({
  active,
  collapsed = false,
  onSelect,
  onExpandSidebar,
  onNavigate,
}: {
  active: boolean
  collapsed?: boolean
  onSelect: () => void
  onExpandSidebar?: () => void
  onNavigate?: () => void
}) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      title={collapsed ? "PnL" : undefined}
      onClick={() => {
        if (collapsed) {
          onExpandSidebar?.()
        }
        onSelect()
        onNavigate?.()
      }}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
        "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
        "active:scale-[0.98]",
        "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
        collapsed && "justify-center px-0",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      )}
    >
      <CircleDollarSign className="size-4 shrink-0" aria-hidden />
      <span className={cn(collapsed && "sr-only")}>PnL</span>
    </button>
  )
}

export function AppNav({
  strategies,
  selectedStrategyId,
  onSelectStrategy,
  activeTab,
  onSelectTab,
}: {
  strategies: Strategy[]
  selectedStrategyId: string | null
  onSelectStrategy: (strategyId: string) => void
  activeTab: AppTab
  onSelectTab: (tab: AppTab) => void
}) {
  const [open, setOpen] = useState(false)
  const [collapsed, setCollapsed] = usePersistentState(
    SIDEBAR_STORAGE_KEY,
    false
  )
  const [screenerExpanded, setScreenerExpanded] = useState(true)
  const titleId = useId()
  const sidebarId = useId()
  const desktopListId = useId()
  const mobileListId = useId()

  return (
    <>
      <aside
        id={sidebarId}
        data-collapsed={collapsed}
        className={cn(
          "material-sidebar text-sidebar-foreground border-sidebar-border hidden shrink-0 flex-col border-r md:flex",
          "transition-[width] duration-200 ease-[var(--ease-out)]",
          collapsed ? "w-16" : "w-56"
        )}
      >
        <div
          className={cn(
            "border-sidebar-border flex items-center gap-2 border-b px-3 py-3",
            collapsed && "justify-center"
          )}
        >
          {collapsed ? null : (
            <div className="min-w-0 flex-1">
              <p className="display-tight truncate text-sm font-semibold">
                Qian Quantitative
              </p>
              <p className="text-muted-foreground mt-0.5 truncate text-xs tracking-wide">
                Screener dashboard
              </p>
            </div>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-expanded={!collapsed}
            aria-controls={sidebarId}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? (
              <PanelLeftOpen aria-hidden />
            ) : (
              <PanelLeftClose aria-hidden />
            )}
          </Button>
        </div>
        <nav aria-label="Primary" className="flex flex-1 flex-col gap-1 p-3">
          <ScreenerNav
            strategies={strategies}
            selectedStrategyId={selectedStrategyId}
            onSelectStrategy={(id) => {
              onSelectTab("screener")
              onSelectStrategy(id)
            }}
            strategyHighlight={activeTab === "screener"}
            collapsed={collapsed}
            expanded={screenerExpanded}
            listId={desktopListId}
            onToggleExpanded={() => setScreenerExpanded((value) => !value)}
            onExpandSidebar={() => setCollapsed(false)}
          />
          <WatchlistsNavButton
            active={activeTab === "watchlists"}
            collapsed={collapsed}
            onSelect={() => onSelectTab("watchlists")}
            onExpandSidebar={() => setCollapsed(false)}
          />
          <DiaryNavButton
            active={activeTab === "diary"}
            collapsed={collapsed}
            onSelect={() => onSelectTab("diary")}
            onExpandSidebar={() => setCollapsed(false)}
          />
          <PositionsNavButton
            active={activeTab === "positions"}
            collapsed={collapsed}
            onSelect={() => onSelectTab("positions")}
            onExpandSidebar={() => setCollapsed(false)}
          />
          <PnlNavButton
            active={activeTab === "pnl"}
            collapsed={collapsed}
            onSelect={() => onSelectTab("pnl")}
            onExpandSidebar={() => setCollapsed(false)}
          />
        </nav>
      </aside>

      <div className="border-border glass-chrome sticky top-0 z-30 flex h-14 items-center gap-2 border-b px-4 md:hidden">
        <Dialog.Root open={open} onOpenChange={setOpen}>
          <Dialog.Trigger
            render={
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={open ? "Close navigation" : "Open navigation"}
              />
            }
          >
            {open ? <X aria-hidden /> : <Menu aria-hidden />}
          </Dialog.Trigger>

          <Dialog.Portal>
            <Dialog.Backdrop className="scrim-enter fixed inset-0 z-40 bg-[var(--scrim)] md:hidden" />
            <Dialog.Popup
              aria-labelledby={titleId}
              className="drawer-enter material-sidebar text-sidebar-foreground border-sidebar-border fixed inset-y-0 left-0 z-50 flex w-[min(18rem,85vw)] flex-col border-r shadow-xl outline-none md:hidden"
            >
              <div className="border-sidebar-border flex items-center justify-between border-b px-4 py-3">
                <div className="min-w-0">
                  <Dialog.Title
                    id={titleId}
                    className="display-tight truncate text-sm font-semibold"
                  >
                    Qian Quantitative
                  </Dialog.Title>
                  <p className="text-muted-foreground truncate text-xs tracking-wide">
                    Screener dashboard
                  </p>
                </div>
                <Dialog.Close
                  render={
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label="Close navigation"
                    />
                  }
                >
                  <X aria-hidden />
                </Dialog.Close>
              </div>
              <nav
                aria-label="Primary"
                className="flex flex-1 flex-col gap-1 p-3"
              >
                <ScreenerNav
                  strategies={strategies}
                  selectedStrategyId={selectedStrategyId}
                  onSelectStrategy={(id) => {
                    onSelectTab("screener")
                    onSelectStrategy(id)
                  }}
                  strategyHighlight={activeTab === "screener"}
                  expanded={screenerExpanded}
                  listId={mobileListId}
                  onToggleExpanded={() =>
                    setScreenerExpanded((value) => !value)
                  }
                  onNavigate={() => setOpen(false)}
                />
                <WatchlistsNavButton
                  active={activeTab === "watchlists"}
                  onSelect={() => onSelectTab("watchlists")}
                  onNavigate={() => setOpen(false)}
                />
                <DiaryNavButton
                  active={activeTab === "diary"}
                  onSelect={() => onSelectTab("diary")}
                  onNavigate={() => setOpen(false)}
                />
                <PositionsNavButton
                  active={activeTab === "positions"}
                  onSelect={() => onSelectTab("positions")}
                  onNavigate={() => setOpen(false)}
                />
                <PnlNavButton
                  active={activeTab === "pnl"}
                  onSelect={() => onSelectTab("pnl")}
                  onNavigate={() => setOpen(false)}
                />
              </nav>
            </Dialog.Popup>
          </Dialog.Portal>
        </Dialog.Root>

        <div className="min-w-0 flex-1">
          <p className="display-tight truncate text-sm font-semibold">
            Qian Quantitative
          </p>
          <p className="text-muted-foreground truncate text-xs tracking-wide">
            Screener dashboard
          </p>
        </div>
        <ThemeToggle />
      </div>
    </>
  )
}
