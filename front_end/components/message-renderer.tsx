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
  Download,
  Search,
} from "lucide-react";

interface MessageRendererProps {
  message: StreamMessage;
}

export function MessageRenderer({ message }: MessageRendererProps) {
  const { type, data } = message;

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
      const downloadLink = `data:application/vnd.google-earth.kmz;base64,${data}`;
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-green-400" />
            <a
              href={downloadLink}
              download="waylines.kmz"
              className="text-sm text-green-300 underline"
            >
              Download Waylines.kmz
            </a>
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

    case "file":
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-green-400" />
            <a
              href={data}
              download="waylines.kmz"
              className="text-sm text-green-300 underline"
            >
              Download Waylines.kmz
            </a>
          </div>
        </div>
      );

    case "prompt_analysis":
      return (
        <div className="space-y-2 bg-zinc-900 p-3 rounded">
          <div className="text-cyan-300">Actor: {data[0]?.actor || "N/A"}</div>
          <div className="text-cyan-300">
            Action: {data[0]?.actions?.[0]?.action || "N/A"}
          </div>
          <div className="text-cyan-300">
            Subjects:{" "}
            {data[0]?.actions?.[0]?.subjects
              ?.map((s: any) => s.subject)
              .join(", ") || "N/A"}
          </div>
          <div className="text-cyan-300">
            Conditions:{" "}
            {data[1]?.actions?.[0]?.subjects
              ?.map((s: any) => s.subject)
              .join(", ") || "N/A"}
          </div>
        </div>
      );

    case "kmz_generation":
      return (
        <div className="flex items-start gap-2">
          <Download className="mt-0.5 h-4 w-4 text-purple-400" />
          <div>
            <p className="text-purple-200">{data}</p>
          </div>
        </div>
      );

    default:
      return (
        <div>
          <p className="text-zinc-100">
            {typeof data === "object" ? JSON.stringify(data) : String(data)}
          </p>
        </div>
      );
  }
}
