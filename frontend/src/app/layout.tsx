import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SpendSense',
  description: 'Explainable Financial Education Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
