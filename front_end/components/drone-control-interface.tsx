"use client";

import type React from "react";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  ImageIcon,
  X,
  Settings,
  Loader2,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter,
} from "@/components/ui/sheet";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useMobile } from "@/hooks/use-mobile";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  sendMessageToApi,
  validateApiUrl,
  type StreamMessage,
} from "@/lib/api";
import { loadSettings, updateSetting } from "@/lib/settings";
import { toast } from "@/hooks/use-toast";
import { MessageRenderer } from "@/components/message-renderer";

type MessageType = {
  id: string;
  sender: "user" | "drone";
  text: string;
  images?: string[];
  timestamp: Date;
  streaming?: boolean;
  streamMessages?: StreamMessage[];
};

export default function DroneControlInterface() {
  // State for messages and input
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: "welcome",
      sender: "drone",
      text: "Welcome to Areon. I'm ready to assist with your drone operations.",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviewUrls, setImagePreviewUrls] = useState<string[]>([]);

  // Settings state
  const [apiUrl, setApiUrl] = useState("");
  const [tempApiUrl, setTempApiUrl] = useState("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Other state
  const [isDragging, setIsDragging] = useState(false);
  const isMobile = useMobile();

  // Load settings on initial render
  useEffect(() => {
    const settings = loadSettings();
    setApiUrl(settings.apiUrl);
    setTempApiUrl(settings.apiUrl);
  }, []);

  // Scroll to bottom of messages when new message is added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle image selection
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setSelectedImages((prev) => [...prev, ...newFiles]);

      // Create preview URLs for the images
      const newPreviewUrls = newFiles.map((file) => URL.createObjectURL(file));
      setImagePreviewUrls((prev) => [...prev, ...newPreviewUrls]);
    }
  };

  // Handle drag events
  useEffect(() => {
    const dropZone = dropZoneRef.current;
    if (!dropZone) return;

    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(true);
    };

    const handleDragLeave = () => {
      setIsDragging(false);
    };

    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (e.dataTransfer?.files) {
        const newFiles = Array.from(e.dataTransfer.files).filter((file) =>
          file.type.startsWith("image/")
        );
        setSelectedImages((prev) => [...prev, ...newFiles]);

        // Create preview URLs for the images
        const newPreviewUrls = newFiles.map((file) =>
          URL.createObjectURL(file)
        );
        setImagePreviewUrls((prev) => [...prev, ...newPreviewUrls]);
      }
    };

    dropZone.addEventListener("dragover", handleDragOver);
    dropZone.addEventListener("dragleave", handleDragLeave);
    dropZone.addEventListener("drop", handleDrop);

    return () => {
      dropZone.removeEventListener("dragover", handleDragOver);
      dropZone.removeEventListener("dragleave", handleDragLeave);
      dropZone.removeEventListener("drop", handleDrop);
    };
  }, []);

  // Remove selected image
  const removeImage = (index: number) => {
    setSelectedImages((prev) => prev.filter((_, i) => i !== index));

    // Revoke the object URL to avoid memory leaks
    URL.revokeObjectURL(imagePreviewUrls[index]);
    setImagePreviewUrls((prev) => prev.filter((_, i) => i !== index));
  };

  // Clear all selected images
  const clearImages = () => {
    // Revoke all object URLs to avoid memory leaks
    imagePreviewUrls.forEach((url) => URL.revokeObjectURL(url));
    setSelectedImages([]);
    setImagePreviewUrls([]);
  };

  // Save API URL settings
  const saveApiSettings = () => {
    if (!validateApiUrl(tempApiUrl)) {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid URL",
        variant: "destructive",
      });
      return;
    }

    setApiUrl(tempApiUrl);
    updateSetting("apiUrl", tempApiUrl);
    setIsSettingsOpen(false);

    toast({
      title: "Settings saved",
      description: "API URL has been updated",
    });
  };

  // Handle sending message
  const handleSendMessage = async () => {
    if ((!inputText.trim() && selectedImages.length === 0) || isLoading) return;

    // Create a new user message
    const newUserMessage: MessageType = {
      id: Date.now().toString(),
      sender: "user",
      text: inputText,
      images: imagePreviewUrls,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInputText("");
    setIsLoading(true);

    // Create a placeholder for the streaming response
    const streamingMessageId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: streamingMessageId,
        sender: "drone",
        text: "",
        timestamp: new Date(),
        streaming: true,
        streamMessages: [],
      },
    ]);
    setIsStreaming(true);

    try {
      // Send message to API
      const response = await sendMessageToApi(
        apiUrl,
        {
          text: inputText,
          images: selectedImages,
        },
        (streamMessage) => {
          // Update the message with the new stream message
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id === streamingMessageId) {
                const updatedStreamMessages = [
                  ...(msg.streamMessages || []),
                  streamMessage,
                ];
                return {
                  ...msg,
                  streamMessages: updatedStreamMessages,
                };
              }
              return msg;
            })
          );
        }
      );

      // Finish streaming
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === streamingMessageId) {
            return {
              ...msg,
              streaming: false,
              streamMessages: response.messages,
            };
          }
          return msg;
        })
      );

      // Clear selected images after sending
      clearImages();
    } catch (error) {
      console.error("Error sending message:", error);

      // Update the streaming message to show an error
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === streamingMessageId) {
            return {
              ...msg,
              text: "Error processing request. Please try again.",
              streaming: false,
            };
          }
          return msg;
        })
      );
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <Card className="mb-4 overflow-hidden border-zinc-800 bg-zinc-900/50 shadow-xl">
        <div className="flex items-center justify-between border-b border-zinc-800 p-4">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 bg-purple-500"></div>
            <h2 className="text-lg font-semibold text-white">
              Drone Communication
            </h2>
          </div>
          <Sheet open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="text-zinc-400 hover:text-white"
              >
                <Settings className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent className="border-zinc-800 bg-zinc-900 text-white">
              <SheetHeader>
                <SheetTitle className="text-white">
                  API Configuration
                </SheetTitle>
                <SheetDescription className="text-zinc-400">
                  Configure the backend API endpoint for drone communication.
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="api-url" className="text-zinc-300">
                    Backend API URL
                  </Label>
                  <Input
                    id="api-url"
                    value={tempApiUrl}
                    onChange={(e) => setTempApiUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="border-zinc-700 bg-zinc-800 text-white"
                  />
                  <p className="text-xs text-zinc-500">
                    Enter the URL of your FastAPI backend server
                  </p>
                </div>
              </div>
              <SheetFooter className="mt-6">
                <Button
                  variant="outline"
                  onClick={() => setIsSettingsOpen(false)}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white"
                >
                  Cancel
                </Button>
                <Button
                  onClick={saveApiSettings}
                  className="bg-purple-600 text-white hover:bg-purple-700"
                >
                  Save Changes
                </Button>
              </SheetFooter>
            </SheetContent>
          </Sheet>
        </div>

        {/* Messages container */}
        <ScrollArea className="h-[400px] p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex animate-fadeIn",
                  message.sender === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] px-4 py-2",
                    message.sender === "user"
                      ? "bg-purple-600 text-white"
                      : "bg-zinc-800 text-zinc-100"
                  )}
                >
                  {message.images && message.images.length > 0 && (
                    <div className="mb-2 grid grid-cols-2 gap-2">
                      {message.images.map((img, index) => (
                        <div key={index} className="relative overflow-hidden">
                          <img
                            src={img || "/placeholder.svg"}
                            alt={`Uploaded image ${index + 1}`}
                            className="h-32 w-full object-cover"
                          />
                        </div>
                      ))}
                    </div>
                  )}

                  {message.streamMessages &&
                  message.streamMessages.length > 0 ? (
                    <div className="space-y-3">
                      {message.streamMessages.map((streamMsg, index) => (
                        <div key={index}>
                          <MessageRenderer message={streamMsg} />
                        </div>
                      ))}
                      {message.streaming && (
                        <div className="mt-1 flex items-center gap-1">
                          <div className="h-1.5 w-1.5 animate-pulse bg-purple-400"></div>
                          <div
                            className="h-1.5 w-1.5 animate-pulse bg-purple-400"
                            style={{ animationDelay: "0.2s" }}
                          ></div>
                          <div
                            className="h-1.5 w-1.5 animate-pulse bg-purple-400"
                            style={{ animationDelay: "0.4s" }}
                          ></div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p>{message.text}</p>
                  )}

                  <p
                    className={cn(
                      "mt-1 text-right text-xs",
                      message.sender === "user"
                        ? "text-purple-200"
                        : "text-zinc-500"
                    )}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Image upload area */}
        <div
          ref={dropZoneRef}
          className={cn(
            "border-t border-zinc-800 bg-zinc-900/80 p-4 transition-all",
            isDragging && "bg-purple-900/20"
          )}
        >
          {selectedImages.length === 0 ? (
            <div
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center border-2 border-dashed border-zinc-700 p-6 transition-all hover:border-purple-500",
                isDragging && "border-purple-500 bg-purple-900/10"
              )}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud className="mb-2 h-8 w-8 text-zinc-500" />
              <p className="mb-1 text-sm font-medium text-zinc-300">
                Drag & drop images or click to upload
              </p>
              <p className="text-xs text-zinc-500">
                Upload drone camera images for analysis
              </p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                multiple
                className="hidden"
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="bg-zinc-800 text-zinc-300">
                  {selectedImages.length}{" "}
                  {selectedImages.length === 1 ? "image" : "images"} selected
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-zinc-400 hover:text-white"
                  onClick={clearImages}
                >
                  <Trash2 className="mr-1 h-4 w-4" />
                  Clear all
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {imagePreviewUrls.map((url, index) => (
                  <div
                    key={index}
                    className="relative h-20 w-20 overflow-hidden"
                  >
                    <img
                      src={url || "/placeholder.svg"}
                      alt={`Preview ${index + 1}`}
                      className="h-full w-full object-cover"
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeImage(index);
                      }}
                      className="absolute right-1 top-1 bg-black/70 p-1 text-white shadow-md transition-all hover:bg-red-500"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
                <div
                  className="flex h-20 w-20 cursor-pointer items-center justify-center border border-dashed border-zinc-700 hover:border-purple-500"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <ImageIcon className="h-6 w-6 text-zinc-500" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <CardContent className="border-t border-zinc-800 p-4">
          <div className="flex items-end gap-2">
            <div className="relative flex-grow">
              {isMobile ? (
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Enter command for drone..."
                  className="border-zinc-700 bg-zinc-800 text-white"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSendMessage();
                    }
                  }}
                />
              ) : (
                <Textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Enter command for drone..."
                  className="min-h-[40px] resize-none border-zinc-700 bg-zinc-800 text-white"
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                />
              )}
            </div>
            <Button
              onClick={handleSendMessage}
              disabled={isLoading}
              className="flex-shrink-0 bg-purple-600 hover:bg-purple-700"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Features showcase */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-zinc-800 bg-zinc-900/30 p-4 shadow-md transition-transform hover:scale-105">
          <div className="mb-2 w-fit bg-purple-900/30 p-2">
            <ImageIcon className="h-5 w-5 text-purple-400" />
          </div>
          <h3 className="mb-1 font-semibold text-white">Image Analysis</h3>
          <p className="text-sm text-zinc-400">
            Upload drone camera images for ML-powered analysis and processing
          </p>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900/30 p-4 shadow-md transition-transform hover:scale-105">
          <div className="mb-2 w-fit bg-purple-900/30 p-2">
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
              <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
              <path d="M21 3v5h-5" />
            </svg>
          </div>
          <h3 className="mb-1 font-semibold text-white">Real-time Updates</h3>
          <p className="text-sm text-zinc-400">
            Receive streaming updates from the drone's ML processing system
          </p>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900/30 p-4 shadow-md transition-transform hover:scale-105">
          <div className="mb-2 w-fit bg-purple-900/30 p-2">
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
          <h3 className="mb-1 font-semibold text-white">Command Interface</h3>
          <p className="text-sm text-zinc-400">
            Send natural language commands to control your drone
          </p>
        </Card>
      </div>
    </div>
  );
}
