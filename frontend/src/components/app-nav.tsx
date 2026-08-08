import { useEffect, useId, useRef, useState } from "react"
import {
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  ScanSearch,
  X,
} from "lucide-react"

import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { usePersistentState } from "@/lib/use-persistent-state"
import { cn } from "@/lib/utils"

const SIDEBAR_STORAGE_KEY = "qq.sidebar.collapsed"

const navItems = [
  { title: "Discover", href: "#discover", icon: ScanSearch, current: true },
] as const

function NavLinks({
  collapsed = false,
  onNavigate,
}: {
  collapsed?: boolean
  onNavigate?: () => void
}) {
  return (
    <ul className="flex flex-col gap-1">
      {navItems.map((item) => (
        <li key={item.title}>
          <a
            href={item.href}
            aria-current={item.current ? "page" : undefined}
            title={collapsed ? item.title : undefined}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              "focus-visible:ring-sidebar-ring outline-none focus-visible:ring-2",
              collapsed && "justify-center px-0",
              item.current
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            )}
          >
            <item.icon className="size-4 shrink-0" aria-hidden />
            <span className={cn(collapsed && "sr-only")}>{item.title}</span>
          </a>
        </li>
      ))}
    </ul>
  )
}

export function AppNav() {
  const [open, setOpen] = useState(false)
  const [collapsed, setCollapsed] = usePersistentState(
    SIDEBAR_STORAGE_KEY,
    false
  )
  const panelId = useId()
  const titleId = useId()
  const sidebarId = useId()
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return

    const menuButton = menuButtonRef.current
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false)
    }

    document.addEventListener("keydown", onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    closeButtonRef.current?.focus()

    return () => {
      document.removeEventListener("keydown", onKeyDown)
      document.body.style.overflow = previousOverflow
      menuButton?.focus()
    }
  }, [open])

  return (
    <>
      <aside
        id={sidebarId}
        data-collapsed={collapsed}
        className={cn(
          "bg-sidebar text-sidebar-foreground border-sidebar-border hidden shrink-0 flex-col border-r transition-[width] duration-200 md:flex",
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
              <p className="truncate text-sm font-semibold tracking-tight">
                Qian Quantitative
              </p>
              <p className="text-muted-foreground mt-0.5 truncate text-xs">
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
        <nav aria-label="Primary" className="flex-1 p-3">
          <NavLinks collapsed={collapsed} />
        </nav>
      </aside>

      <div className="border-border bg-background sticky top-0 z-30 flex h-14 items-center gap-2 border-b px-4 md:hidden">
        <Button
          ref={menuButtonRef}
          type="button"
          variant="ghost"
          size="icon"
          aria-expanded={open}
          aria-controls={panelId}
          aria-haspopup="dialog"
          aria-label={open ? "Close navigation" : "Open navigation"}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X aria-hidden /> : <Menu aria-hidden />}
        </Button>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">Qian Quantitative</p>
          <p className="text-muted-foreground truncate text-xs">
            Screener dashboard
          </p>
        </div>
        <ThemeToggle />
      </div>

      {open ? (
        <div className="fixed inset-0 z-40 md:hidden" role="presentation">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
          />
          <div
            id={panelId}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="bg-sidebar text-sidebar-foreground border-sidebar-border absolute inset-y-0 left-0 flex w-[min(18rem,85vw)] flex-col border-r shadow-lg"
          >
            <div className="border-sidebar-border flex items-center justify-between border-b px-4 py-3">
              <div className="min-w-0">
                <p id={titleId} className="truncate text-sm font-semibold">
                  Qian Quantitative
                </p>
                <p className="text-muted-foreground truncate text-xs">
                  Screener dashboard
                </p>
              </div>
              <Button
                ref={closeButtonRef}
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Close navigation"
                onClick={() => setOpen(false)}
              >
                <X aria-hidden />
              </Button>
            </div>
            <nav aria-label="Primary" className="flex-1 p-3">
              <NavLinks onNavigate={() => setOpen(false)} />
            </nav>
          </div>
        </div>
      ) : null}
    </>
  )
}
