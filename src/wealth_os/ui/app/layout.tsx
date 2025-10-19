import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { DashboardProvider } from "@/components/dashboard-provider";
import { PageTransition } from "@/components/page-transition";
import { ThemeProvider } from "next-themes";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WealthOS",
  description: "WealthOS — modern portfolio tracking and insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`} suppressHydrationWarning>
        <SidebarProvider
          style={{
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties}
        >
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <AppSidebar variant="inset" />
            <SidebarInset>
              <DashboardProvider>
                <SiteHeader />
                <div className="flex flex-1 flex-col p-4 lg:p-6">
                  <PageTransition>
                    <div className="mx-auto w-full max-w-5xl">{children}</div>
                  </PageTransition>
                </div>
              </DashboardProvider>
            </SidebarInset>
          </ThemeProvider>
        </SidebarProvider>
        <Toaster richColors closeButton position="top-right" />
      </body>
    </html>
  );
}
