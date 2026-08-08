import { AppNav } from "@/components/app-nav"
import { DiscoverScreener } from "@/components/discover-screener"
import { ThemeToggle } from "@/components/theme-toggle"

export default function App() {
  return (
    <div className="bg-background text-foreground flex min-h-svh w-full flex-col md:flex-row">
      <AppNav />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-border hidden h-14 shrink-0 items-center justify-between gap-4 border-b px-6 md:flex">
          <div>
            <h1 className="text-sm font-semibold tracking-tight">Discover</h1>
            <p className="text-muted-foreground text-xs">
              Run the hybrid screener and review candidates
            </p>
          </div>
          <ThemeToggle />
        </header>

        <main className="flex-1 overflow-y-auto">
          <DiscoverScreener />
        </main>
      </div>
    </div>
  )
}
