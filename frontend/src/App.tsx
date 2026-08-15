import { useEffect, useState } from "react"

import { AppNav, type AppTab } from "@/components/app-nav"
import { DiaryPanel } from "@/components/diary-panel"
import { PositionsPanel } from "@/components/positions-panel"
import { ScreenerPanel } from "@/components/screener-panel"
import { WatchlistsPanel } from "@/components/watchlists-panel"
import { ThemeToggle } from "@/components/theme-toggle"
import { listStrategies, type Strategy } from "@/lib/screener-api"
import { usePersistentState } from "@/lib/use-persistent-state"

export default function App() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [strategiesError, setStrategiesError] = useState<string | null>(null)
  const [strategiesLoading, setStrategiesLoading] = useState(true)
  const [strategyId, setStrategyId] = usePersistentState<string | null>(
    "qq.screener.strategy",
    null
  )
  const [activeTab, setActiveTab] = usePersistentState<AppTab>(
    "qq.app.tab",
    "screener"
  )
  // Mount each tab panel on first visit, then keep it mounted (hidden) so
  // switching tabs does not remount or refetch.
  const [mountedTabs, setMountedTabs] = useState<Record<AppTab, boolean>>(
    () => ({
      screener: activeTab === "screener",
      diary: activeTab === "diary",
      positions: activeTab === "positions",
      watchlists: activeTab === "watchlists",
    })
  )
  if (!mountedTabs[activeTab]) {
    setMountedTabs({ ...mountedTabs, [activeTab]: true })
  }

  useEffect(() => {
    const controller = new AbortController()
    listStrategies(controller.signal)
      .then((list) => {
        setStrategies(list)
        setStrategiesError(null)
        setStrategyId((current) => {
          if (current != null && list.some((item) => item.id === current)) {
            return current
          }
          return list[0]?.id ?? null
        })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setStrategiesError(
          error instanceof Error ? error.message : "Something went wrong."
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setStrategiesLoading(false)
      })
    return () => controller.abort()
  }, [setStrategyId])

  const activeStrategy =
    strategies.find((item) => item.id === strategyId) ?? null

  return (
    <div className="bg-background text-foreground flex min-h-svh w-full flex-col md:flex-row">
      <AppNav
        strategies={strategies}
        selectedStrategyId={strategyId}
        onSelectStrategy={setStrategyId}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-border glass-chrome sticky top-0 z-20 hidden h-14 shrink-0 items-center justify-between gap-4 border-b px-6 md:flex">
          <div>
            <h1 className="display-tight text-sm font-semibold">
              {activeTab === "watchlists"
                ? "Watchlists"
                : activeTab === "diary"
                  ? "Market Diary"
                  : activeTab === "positions"
                    ? "Position Management"
                    : (activeStrategy?.label ?? "Screener")}
            </h1>
            {activeTab === "screener" ? (
              <p className="text-muted-foreground text-xs tracking-wide">
                {activeStrategy?.description}
              </p>
            ) : activeTab === "positions" ? (
              <p className="text-muted-foreground text-xs tracking-wide">
                Sizing and profit-taking plan
              </p>
            ) : activeTab === "watchlists" ? (
              <p className="text-muted-foreground text-xs tracking-wide">
                Master, stalk, focus, back
              </p>
            ) : (
              <p className="text-muted-foreground text-xs tracking-wide">
                Pre-open situational awareness
              </p>
            )}
          </div>
          <ThemeToggle />
        </header>

        <main className="flex-1 overflow-y-auto">
          {mountedTabs.diary ? (
            <div hidden={activeTab !== "diary"}>
              <DiaryPanel />
            </div>
          ) : null}
          {mountedTabs.watchlists ? (
            <div hidden={activeTab !== "watchlists"}>
              <WatchlistsPanel />
            </div>
          ) : null}
          {mountedTabs.positions ? (
            <div hidden={activeTab !== "positions"}>
              <PositionsPanel />
            </div>
          ) : null}
          {mountedTabs.screener ? (
            <div hidden={activeTab !== "screener"}>
              {strategiesLoading ? (
                <p className="text-muted-foreground p-6 text-sm">
                  Loading strategies…
                </p>
              ) : strategiesError ? (
                <p role="alert" className="text-destructive p-6 text-sm">
                  {strategiesError}
                </p>
              ) : activeStrategy ? (
                <ScreenerPanel
                  key={activeStrategy.id}
                  strategy={activeStrategy}
                />
              ) : null}
            </div>
          ) : null}
        </main>
      </div>
    </div>
  )
}
