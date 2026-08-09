import { useEffect, useState } from "react"

import { AppNav } from "@/components/app-nav"
import { ScreenerPanel } from "@/components/screener-panel"
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
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-border hidden h-14 shrink-0 items-center justify-between gap-4 border-b px-6 md:flex">
          <div>
            <h1 className="text-sm font-semibold tracking-tight">
              {activeStrategy?.label ?? "Screener"}
            </h1>
            <p className="text-muted-foreground text-xs">
              {activeStrategy?.description}
            </p>
          </div>
          <ThemeToggle />
        </header>

        <main className="flex-1 overflow-y-auto">
          {strategiesLoading ? (
            <p className="text-muted-foreground p-6 text-sm">
              Loading strategies…
            </p>
          ) : strategiesError ? (
            <p role="alert" className="text-destructive p-6 text-sm">
              {strategiesError}
            </p>
          ) : activeStrategy ? (
            <ScreenerPanel key={activeStrategy.id} strategy={activeStrategy} />
          ) : null}
        </main>
      </div>
    </div>
  )
}
