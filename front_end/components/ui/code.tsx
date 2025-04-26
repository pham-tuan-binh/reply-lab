import * as React from "react"
import { cn } from "@/lib/utils"

interface CodeProps extends React.HTMLAttributes<HTMLPreElement> {
  children: React.ReactNode
}

const Code = React.forwardRef<HTMLPreElement, CodeProps>(({ className, children, ...props }, ref) => {
  return (
    <pre ref={ref} className={cn("overflow-auto bg-zinc-950 p-4 font-mono text-sm text-zinc-50", className)} {...props}>
      <code>{children}</code>
    </pre>
  )
})
Code.displayName = "Code"

export { Code }
