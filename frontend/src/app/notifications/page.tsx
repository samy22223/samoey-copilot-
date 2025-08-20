'use client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bell, Check } from 'lucide-react'

export default function NotificationsPage() {
  const notifications = [
    { id: 1, title: "Welcome to Samoey Copilot", message: "Get started with our AI features", time: "2 hours ago" },
    { id: 2, title: "New Feature Available", message: "Check out our latest AI capabilities", time: "1 day ago" },
  ]

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center mb-8">
        <Bell className="h-8 w-8 mr-3" />
        <h1 className="text-3xl font-bold">Notifications
