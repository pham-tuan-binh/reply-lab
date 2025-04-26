"use client";

import type { StreamMessage } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Code } from "@/components/ui/code";
import {
  AlertCircle,
  CheckCircle,
  Info,
  Terminal,
  ImageIcon,
} from "lucide-react";

interface MessageRendererProps {
  message: StreamMessage;
}

export function MessageRenderer({ message }: MessageRendererProps) {
  const { type, data } = message;

  // Render based on message type
  switch (type) {
    case "status":
      return (
        <div className="flex items-start gap-2">
          <Terminal className="mt-0.5 h-4 w-4 text-purple-400" />
          <div>
            <p className="text-zinc-100">{data}</p>
          </div>
        </div>
      );

    case "log":
      return (
        <div className="flex items-start gap-2">
          <Terminal className="mt-0.5 h-4 w-4 text-zinc-400" />
          <div>
            <p className="font-mono text-sm text-zinc-400">{data}</p>
          </div>
        </div>
      );

    case "info":
      return (
        <div className="flex items-start gap-2">
          <Info className="mt-0.5 h-4 w-4 text-blue-400" />
          <div>
            <p className="text-zinc-100">{data}</p>
          </div>
        </div>
      );

    case "warning":
      return (
        <div className="flex items-start gap-2">
          <AlertCircle className="mt-0.5 h-4 w-4 text-yellow-400" />
          <div>
            <p className="text-yellow-200">{data}</p>
          </div>
        </div>
      );

    case "error":
      return (
        <div className="flex items-start gap-2">
          <AlertCircle className="mt-0.5 h-4 w-4 text-red-400" />
          <div>
            <p className="text-red-200">{data}</p>
          </div>
        </div>
      );

    case "success":
      return (
        <div className="flex items-start gap-2">
          <CheckCircle className="mt-0.5 h-4 w-4 text-green-400" />
          <div>
            <p className="text-green-200">{data}</p>
          </div>
        </div>
      );

    case "data":
      return (
        <div className="space-y-1">
          <Badge variant="outline" className="mb-1 bg-zinc-800 text-zinc-300">
            Telemetry Data
          </Badge>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(data).map(([key, value]) => {
              if (typeof value === "object" && value !== null) {
                return (
                  <div key={key} className="col-span-2 space-y-1">
                    <p className="text-xs text-zinc-400">{key}:</p>
                    <Code className="bg-zinc-900 text-xs">
                      {JSON.stringify(value, null, 2)}
                    </Code>
                  </div>
                );
              }
              return (
                <div
                  key={key}
                  className="flex items-center justify-between bg-zinc-900 p-2"
                >
                  <span className="text-xs text-zinc-400">{key}</span>
                  <span className="text-sm text-zinc-100">{String(value)}</span>
                </div>
              );
            })}
          </div>
        </div>
      );

    case "image":
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ImageIcon className="h-4 w-4 text-blue-400" />
            <span className="text-sm text-zinc-300">Drone Camera Feed</span>
          </div>
          <div className="overflow-hidden border border-zinc-700">
            <img
              src={data || "/placeholder.svg"}
              alt="Drone camera feed"
              className="h-auto w-full"
            />
          </div>
        </div>
      );

    default:
      // Default renderer for unknown types
      return (
        <div>
          <p className="text-zinc-100">
            {typeof data === "object" ? JSON.stringify(data) : String(data)}
          </p>
        </div>
      );
  }
}
