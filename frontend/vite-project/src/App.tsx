import { AppSidebar } from "@/components/sidebar"
import { IndicatorTable } from "./components/indicatortable"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function Page() {
  return (
    <div className="min-h-screen w-full flex">
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="flex-1">
          <header className="flex h-14 shrink-0 items-center gap-2 border-b">
            <div className="flex flex-1 items-center gap-2 px-4">
              <SidebarTrigger />
              <Separator orientation="vertical" className="h-6" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbPage className="line-clamp-1">
                      Technical Analysis
                    </BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          
          {/* Main content container */}
          <main className="flex-1 overflow-y-auto">
            <div className="container mx-auto px-8 py-8">
              <div className="max-w-7xl mx-auto space-y-8">
                {/* Search section */}
                <div className="flex gap-2 max-w-md mx-auto">
                  <Input placeholder="Search Ticker" className="flex-1" />
                  <Button type="submit">Search</Button>
                </div>

                {/* Indicators section */}
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold px-6">Indicators</h2>
                  <div className="bg-muted/50 rounded-xl p-6">
                    <IndicatorTable />
                  </div>
                </div>
              </div>
            </div>
          </main>
        </SidebarInset>
      </SidebarProvider>
    </div>
  )
}
