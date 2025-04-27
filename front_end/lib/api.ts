// API functions for drone control app

// Types
export type MessageRequest = {
  text: string;
  images?: File[];
};

export type StreamMessage = {
  type: string;
  data: any;
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

    let collectedMessages: StreamMessage[] = [];

    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        try {
          const parsed = JSON.parse(event.data);
          onStreamMessage?.(parsed);
          collectedMessages.push(parsed);
        } catch {
          onStreamMessage?.({ type: "log", data: event.data });
          collectedMessages.push({ type: "log", data: event.data });
        }
      } else if (event.data instanceof ArrayBuffer) {
        const blob = new Blob([event.data], {
          type: "application/vnd.google-earth.kmz",
        });
        const url = URL.createObjectURL(blob);
        const fileMessage: StreamMessage = { type: "file", data: url };
        onStreamMessage?.(fileMessage);
        collectedMessages.push(fileMessage);
      }
    };

    ws.onerror = () => {
      reject({
        messages: [{ type: "error", data: "WebSocket error." }],
        status: "error",
      });
    };

    ws.onclose = () => {
      resolve({
        messages: collectedMessages,
        status: "success",
      });
    };
  });
}
