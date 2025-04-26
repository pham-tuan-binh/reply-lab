// API functions for drone control app

// Types
export type MessageRequest = {
  text: string;
  images?: File[];
};

export type StreamMessage = {
  type: string;
  data: any; // Can be string, object, or any other data type
};

export type MessageResponse = {
  messages: StreamMessage[];
  status: "success" | "error";
};

export async function sendMessageToApi(
  apiUrl: string,
  request: MessageRequest,
  onStreamMessage?: (message: StreamMessage) => void
): Promise<MessageResponse> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(apiUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = async () => {
      try {
        ws.send(`PROMPT:${request.text}`);

        if (request.images?.length) {
          for (const image of request.images) {
            ws.send(`FILENAME:${image.name}`);
            const buffer = await image.arrayBuffer();
            ws.send(buffer);
          }
        }

        ws.send("UPLOAD_COMPLETE");
      } catch (e) {
        reject({
          messages: [{ type: "error", data: String(e) }],
          status: "error",
        });
      }
    };

    let fullMessage = "";

    ws.onmessage = (event) => {
      const data =
        typeof event.data === "string" ? event.data : "[binary data]";
      fullMessage += data;
      onStreamMessage?.({ type: "stream", data });
    };

    ws.onerror = (error) => {
      reject({
        messages: [{ type: "error", data: "WebSocket error." }],
        status: "error",
      });
    };

    ws.onclose = () => {
      resolve({
        messages: [{ type: "success", data: fullMessage }],
        status: "success",
      });
    };
  });
}

// Function to simulate streaming response (for demo purposes)
async function simulateStreamingResponse(
  onStreamMessage?: (message: StreamMessage) => void
): Promise<MessageResponse> {
  const messages: StreamMessage[] = [
    {
      type: "status",
      data: "Initializing drone systems",
    },
    {
      type: "log",
      data: "System log: Starting image analysis module",
    },
    {
      type: "info",
      data: "Processing image data from drone camera",
    },
    {
      type: "data",
      data: {
        battery: "87%",
        altitude: "120m",
        speed: "15km/h",
        coordinates: { lat: 37.7749, lng: -122.4194 },
      },
    },
    {
      type: "warning",
      data: "Wind speed increasing in target area",
    },
    {
      type: "image",
      data: "/placeholder.svg?height=200&width=300",
    },
    {
      type: "status",
      data: "Calculating optimal flight path",
    },
    {
      type: "log",
      data: "System log: Path calculation complete",
    },
    {
      type: "success",
      data: "Command processed successfully. Drone executing instructions.",
    },
  ];

  const allMessages: StreamMessage[] = [];

  for (let i = 0; i < messages.length; i++) {
    // Add a delay between messages
    await new Promise((resolve) => setTimeout(resolve, 500));

    const message = messages[i];
    allMessages.push(message);

    // Call the onStreamMessage callback if provided
    if (onStreamMessage) {
      onStreamMessage(message);
    }
  }

  return {
    messages: allMessages,
    status: "success",
  };
}

// Function to validate API URL
export function validateApiUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch (e) {
    return false;
  }
}
