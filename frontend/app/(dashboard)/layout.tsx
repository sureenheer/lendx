import type React from "react"
import { SidebarProvider } from "@/components/ui/sidebar"
import { MobileHeader } from "@/components/dashboard/mobile-header"
import { DashboardSidebar } from "@/components/dashboard/sidebar"
import mockDataJson from "@/mock.json"
import type { MockData } from "@/types/dashboard"
import Widget from "@/components/dashboard/widget"
import Notifications from "@/components/dashboard/notifications"
import { MobileChat } from "@/components/chat/mobile-chat"
import Chat from "@/components/chat"
import { DemoProvider } from "@/lib/demo-context"

const mockData = mockDataJson as MockData

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <DemoProvider>
      <SidebarProvider>
        {/* Mobile Header - only visible on mobile */}
        <MobileHeader mockData={mockData} />

        {/* Desktop Layout */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-gap lg:px-sides">
          <div className="hidden lg:block col-span-2 top-0 relative">
            <DashboardSidebar />
          </div>
          <div className="col-span-1 lg:col-span-7">{children}</div>
          <div className="col-span-3 hidden lg:block relative">
            <div className="space-y-gap py-sides min-h-screen max-h-screen sticky top-0 overflow-clip">
              <Widget widgetData={mockData.widgetData} />
              <Notifications initialNotifications={[]} />
              <Chat />
            </div>
          </div>
        </div>

        {/* Mobile Chat - floating CTA with drawer */}
        <MobileChat />
      </SidebarProvider>
    </DemoProvider>
  )
}
