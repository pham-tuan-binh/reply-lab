"use client";
import DroneControlInterface from "@/components/drone-control-interface";
import { ThemeProvider } from "@/components/theme-provider";

export default function Home() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <main className="min-h-screen bg-gradient-to-b from-black to-zinc-900 text-white">
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8">
            <div className="mx-auto flex max-w-4xl items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative h-10 w-10 overflow-hidden rounded-full bg-purple-500/20">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-5 w-5 text-purple-400"
                    >
                      <path d="M12 2c1.5 0 3 .5 3 2-2 0-6 0-6 0 0-1.5 1.5-2 3-2zm3 4c0 1-1 2-3 2s-3-1-3-2m-3 4v10c0 1 0 2 2 2h8c2 0 2-1 2-2V10m-12 2c-1.5 0-3 0-3-2 0-1 .5-2 2-2 0 0 2.5 0 5 0M12 12v6m-3-3h6" />
                    </svg>
                  </div>
                </div>
                <h1 className="text-2xl font-bold tracking-tight">Areon</h1>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-sm text-zinc-400">System Online</span>
              </div>
            </div>
          </header>

          <DroneControlInterface />
        </div>
      </main>
    </ThemeProvider>
  );
}
