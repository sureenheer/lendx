"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Bullet } from "@/components/ui/bullet"
import { X } from "lucide-react"
import { AnimatePresence, motion } from "framer-motion"
import { useDemoContext } from "@/lib/demo-context"

interface DisplayNotification {
  id: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: number
  read: boolean
}

export default function DemoNotifications() {
  const { notifications: demoNotifications, clearNotifications } = useDemoContext()
  const [displayNotifications, setDisplayNotifications] = useState<DisplayNotification[]>([])
  const [showAll, setShowAll] = useState(false)

  // Convert demo notifications to display format
  useEffect(() => {
    const converted = demoNotifications.map((notif, index) => ({
      id: `notif-${notif.timestamp || Date.now()}-${index}`,
      message: notif.message,
      type: notif.type,
      timestamp: notif.timestamp || Date.now(),
      read: false,
    }))
    setDisplayNotifications(converted)
  }, [demoNotifications])

  const unreadCount = displayNotifications.filter((n) => !n.read).length
  const displayedNotifications = showAll
    ? displayNotifications
    : displayNotifications.slice(0, 3)

  const markAsRead = (id: string) => {
    setDisplayNotifications((prev) =>
      prev.map((notif) => (notif.id === id ? { ...notif, read: true } : notif))
    )
  }

  const deleteNotification = (id: string) => {
    setDisplayNotifications((prev) => prev.filter((notif) => notif.id !== id))
  }

  const clearAll = () => {
    setDisplayNotifications([])
    clearNotifications()
  }

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-500/10 border-green-500/20'
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/20'
      case 'error':
        return 'bg-red-500/10 border-red-500/20'
      default:
        return 'bg-blue-500/10 border-blue-500/20'
    }
  }

  return (
    <Card>
      <CardHeader className="flex items-center justify-between pl-3 pr-1">
        <CardTitle className="flex items-center gap-2.5 text-sm font-medium uppercase">
          {unreadCount > 0 ? <Badge>{unreadCount}</Badge> : <Bullet />}
          Notifications
        </CardTitle>
        {displayNotifications.length > 0 && (
          <Button
            className="opacity-50 hover:opacity-100 uppercase"
            size="sm"
            variant="ghost"
            onClick={clearAll}
          >
            Clear All
          </Button>
        )}
      </CardHeader>
      <CardContent className="bg-accent p-1.5 overflow-hidden">
        <div className="space-y-2">
          <AnimatePresence initial={false} mode="popLayout">
            {displayedNotifications.map((notification) => (
              <motion.div
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                key={notification.id}
                className={`relative p-3 rounded-lg border ${getNotificationColor(notification.type)} ${
                  notification.read ? "opacity-50" : ""
                }`}
                onClick={() => markAsRead(notification.id)}
              >
                <p className="text-sm pr-6">{notification.message}</p>
                <Button
                  size="icon"
                  variant="ghost"
                  className="absolute top-2 right-2 size-5"
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteNotification(notification.id)
                  }}
                >
                  <X className="size-3" />
                </Button>
              </motion.div>
            ))}

            {displayNotifications.length === 0 && (
              <div className="text-center py-8">
                <p className="text-sm text-muted-foreground">
                  No notifications
                </p>
              </div>
            )}

            {displayNotifications.length > 3 && (
              <motion.div
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="pt-2"
              >
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAll(!showAll)}
                  className="w-full"
                >
                  {showAll ? "Show Less" : `Show All (${displayNotifications.length})`}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </CardContent>
    </Card>
  )
}
