'use client'
import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Bell, Check, Trash2, Settings, Mail, MessageSquare, AlertTriangle } from 'lucide-react'

interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  time: string
  read: boolean
  actions?: Array<{ label: string; action: () => void }>
}

interface NotificationPreference {
  id: string
  name: string
  description: string
  enabled: boolean
  icon: React.ReactNode
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      title: 'Welcome to Samoey Copilot',
      message: 'Get started with our AI-powered development platform',
      type: 'success',
      time: '2 hours ago',
      read: false
    },
    {
      id: '2',
      title: 'New Feature Available',
      message: 'Check out our latest AI capabilities and improvements',
      type: 'info',
      time: '1 day ago',
      read: false
    },
    {
      id: '3',
      title: 'Security Alert',
      message: 'New login detected from unrecognized device',
      type: 'warning',
      time: '2 days ago',
      read: true
    },
    {
      id: '4',
      title: 'System Maintenance',
      message: 'Scheduled maintenance this weekend. Service may be temporarily unavailable.',
      type: 'error',
      time: '3 days ago',
      read: true
    }
  ])

  const [preferences, setPreferences] = useState<NotificationPreference[]>([
    {
      id: 'email',
      name: 'Email Notifications',
      description: 'Receive notifications via email',
      enabled: true,
      icon: <Mail className="h-4 w-4" />
    },
    {
      id: 'push',
      name: 'Push Notifications',
      description: 'Receive browser push notifications',
      enabled: true,
      icon: <Bell className="h-4 w-4" />
    },
    {
      id: 'chat',
      name: 'Chat Messages',
      description: 'Get notified about new chat messages',
      enabled: false,
      icon: <MessageSquare className="h-4 w-4" />
    },
    {
      id: 'security',
      name: 'Security Alerts',
      description: 'Important security-related notifications',
      enabled: true,
      icon: <AlertTriangle className="h-4 w-4" />
    }
  ])

  const [showPreferences, setShowPreferences] = useState(false)

  const markAsRead = (id: string) => {
    setNotifications(notifications.map(n =>
      n.id === id ? { ...n, read: true } : n
    ))
  }

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })))
  }

  const deleteNotification = (id: string) => {
    setNotifications(notifications.filter(n => n.id !== id))
  }

  const clearAllNotifications = () => {
    setNotifications([])
  }

  const togglePreference = (id: string) => {
    setPreferences(preferences.map(p =>
      p.id === id ? { ...p, enabled: !p.enabled } : p
    ))
  }

  const unreadCount = notifications.filter(n => !n.read).length

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <Check className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <Bell className="h-4 w-4 text-blue-500" />
    }
  }

  const getNotificationColor = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return 'border-green-200 bg-green-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      case 'error':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-blue-200 bg-blue-50'
    }
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center">
          <Bell className="h-8 w-8 mr-3" />
          <div>
            <h1 className="text-3xl font-bold">Notifications</h1>
            {unreadCount > 0 && (
              <p className="text-sm text-muted-foreground">
                {unreadCount} unread notification{unreadCount > 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <Button variant="outline" onClick={markAllAsRead}>
              Mark all as read
            </Button>
          )}
          {notifications.length > 0 && (
            <Button variant="outline" onClick={clearAllNotifications}>
              <Trash2 className="h-4 w-4 mr-2" />
              Clear all
            </Button>
          )}
          <Button
            variant={showPreferences ? "default" : "outline"}
            onClick={() => setShowPreferences(!showPreferences)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Preferences
          </Button>
        </div>
      </div>

      {showPreferences ? (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Notification Preferences</CardTitle>
            <CardDescription>
              Choose how you want to receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {preferences.map((preference) => (
              <div key={preference.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {preference.icon}
                  <div>
                    <h4 className="font-medium">{preference.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {preference.description}
                    </p>
                  </div>
                </div>
                <Switch
                  checked={preference.enabled}
                  onCheckedChange={() => togglePreference(preference.id)}
                />
              </div>
            ))}
          </CardContent>
        </Card>
      ) : (
        <>
          {notifications.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bell className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No notifications</h3>
                <p className="text-muted-foreground text-center">
                  You're all caught up! We'll notify you when there's something new.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {notifications.map((notification) => (
                <Card
                  key={notification.id}
                  className={`transition-all hover:shadow-md ${getNotificationColor(notification.type)} ${!notification.read ? 'border-l-4 border-l-blue-500' : ''}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        {getNotificationIcon(notification.type)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium">{notification.title}</h3>
                            {!notification.read && (
                              <Badge variant="secondary" className="text-xs">
                                New
                              </Badge>
                            )}
                          </div>
                          <p className="text-muted-foreground mb-2">
                            {notification.message}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {notification.time}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {!notification.read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => markAsRead(notification.id)}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteNotification(notification.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
