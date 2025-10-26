"use client"

import type * as React from "react"
import { useIsV0 } from "@/lib/v0-context"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import BracketsIcon from "@/components/icons/brackets"
import GearIcon from "@/components/icons/gear"
import { Bullet } from "@/components/ui/bullet"
import LockIcon from "@/components/icons/lock"
import { Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useDemoContext } from "@/lib/demo-context"

const data = {
  navMain: [
    {
      title: "Navigation",
      items: [
        {
          title: "Dashboard",
          url: "/dashboard",
          icon: BracketsIcon,
          isActive: true,
        },
        {
          title: "Settings",
          url: "/settings",
          icon: GearIcon,
          isActive: false,
          locked: true,
        },
      ],
    },
  ],
}

interface DashboardSidebarProps extends React.ComponentProps<typeof Sidebar> {}

export function DashboardSidebar({ className, ...props }: DashboardSidebarProps) {
  const isV0 = useIsV0()
  const { viewMode, setViewMode, handleNextAction } = useDemoContext()

  return (
    <Sidebar {...props} className={cn("py-sides", className)}>
      <SidebarContent>
        <SidebarGroup className="rounded-t-none">
          <SidebarGroupLabel>
            <Bullet className="mr-2" />
            View Mode
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="flex gap-2 p-2">
              <Button
                variant={viewMode === "lender" ? "default" : "outline"}
                size="sm"
                className="flex-1"
                onClick={() => setViewMode("lender")}
              >
                Lender
              </Button>
              <Button
                variant={viewMode === "borrower" ? "default" : "outline"}
                size="sm"
                className="flex-1"
                onClick={() => setViewMode("borrower")}
              >
                Borrower
              </Button>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>

        {data.navMain.map((group, i) => (
          <SidebarGroup key={group.title}>
            <SidebarGroupLabel>
              <Bullet className="mr-2" />
              {group.title}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem
                    key={item.title}
                    className={cn(item.locked && "pointer-events-none opacity-50", isV0 && "pointer-events-none")}
                    data-disabled={item.locked}
                  >
                    <SidebarMenuButton
                      asChild={!item.locked}
                      isActive={item.isActive}
                      disabled={item.locked}
                      className={cn("disabled:cursor-not-allowed", item.locked && "pointer-events-none")}
                    >
                      {item.locked ? (
                        <div className="flex items-center gap-3 w-full">
                          <item.icon className="size-5" />
                          <span>{item.title}</span>
                        </div>
                      ) : (
                        <a href={item.url}>
                          <item.icon className="size-5" />
                          <span>{item.title}</span>
                        </a>
                      )}
                    </SidebarMenuButton>
                    {item.locked && (
                      <SidebarMenuBadge>
                        <LockIcon className="size-5 block" />
                      </SidebarMenuBadge>
                    )}
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-0">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <Button
                  onClick={() => {
                    console.log("[v0] Button clicked in sidebar")
                    handleNextAction()
                  }}
                  size="lg"
                  className="w-full shadow-lg border-2 border-primary/30"
                >
                  <Play className="size-5" />
                </Button>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
