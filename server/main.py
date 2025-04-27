from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
import shutil
from pathlib import Path
import asyncio
import json
import os
from fastapi.middleware.cors import CORSMiddleware
from modules import process_user_input, generate_kmz, drone_object_detection
import base64

app = FastAPI()
# Allow frontend running on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def process_uploads(websocket: WebSocket, upload_dir: str, prompt: str, files: List[str]):
    """Simple function to process uploaded files and send updates via websocket"""
    try:
        # Send processing started message
        
        # Add your actual processing logic here
        # This is where you'd handle the files based on the prompt
        print(f"Processing files: {files} with prompt: {prompt}")
        print(f"Files are located in: {upload_dir}")
        # replace print and add after it

        image_dir = Path(upload_dir)
        label_dir = image_dir  / "labels"
        output_dir = image_dir.parent / "output"

        label_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)

        # Payload
        payload = {
            "type": "drone_object_detection",
            "data": "Drone object detection in progress..."
        }

        await websocket.send_text(json.dumps(payload))

        drone_object_detection(image_dir, label_dir)

        # Payload
        payload = {
            "type": "kmz_generation",
            "data": "KMZ generation in progress..."
        }

        await websocket.send_text(json.dumps(payload))

        # Generate KMZ file
        generate_kmz(image_dir, label_dir, output_dir)

        output_file = output_dir / "Group14.kmz"
        
        with open(output_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        await websocket.send_text(json.dumps({
            "type": "data",
            "data": encoded
        }))

        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": f"Processing error: {str(e)}",
            "upload_dir": upload_dir
        }))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    prompt = ""
    current_file: Optional[str] = None
    file_writer = None
    uploaded_files: List[str] = []
    
    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                # Handle metadata text message
                data = message["text"]
                
                if data.startswith("PROMPT:"):
                    prompt = data.replace("PROMPT:", "").strip()
                    analysis = process_user_input(prompt)  # Call the LLM processing function

                    payload = {
                        "type": "prompt_analysis",
                        "data": analysis
                    }

                    await websocket.send_text(json.dumps(payload))
                
                elif data.startswith("FILENAME:"):
                    # Close any previously open file writer
                    if file_writer:
                        file_writer.close()
                        file_writer = None
                        uploaded_files.append(current_file)
                    
                    filename = data.replace("FILENAME:", "").strip()
                    save_path = UPLOAD_DIR / filename
                    file_writer = save_path.open("wb")
                    current_file = filename
                
                elif data == "UPLOAD_COMPLETE":
                    # Close the current file if one is open
                    if file_writer:
                        file_writer.close()
                        file_writer = None
                        if current_file:
                            uploaded_files.append(current_file)
                            current_file = None
                    
                    # Create a session folder for this upload batch
                    session_id = f"session_{int(asyncio.get_event_loop().time())}"
                    session_dir = os.path.join(str(UPLOAD_DIR.absolute()), session_id)
                    os.makedirs(session_dir, exist_ok=True)
                    
                    # Move uploaded files to the session directory
                    for file in uploaded_files:
                        source = os.path.join(str(UPLOAD_DIR.absolute()), file)
                        destination = os.path.join(session_dir, file)
                        shutil.move(source, destination)
                    
                    # Send initial response
                    await websocket.send_text(json.dumps({
                        "type": "success",
                        "data": f"Files uploaded successfully to {session_dir}",
                    }))
                    
                    # Process uploads directly (no background task)
                    await process_uploads(websocket, session_dir, prompt, uploaded_files)
                
            elif "bytes" in message and file_writer is not None:
                # Handle binary file chunk
                chunk = message["bytes"]
                try:
                    file_writer.write(chunk)
                except Exception as e:
                    await websocket.send_text(f"Error writing file: {str(e)}")
            
            else:
                await websocket.send_text("Unknown message type or no file currently open")
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        # Ensure any open file is properly closed
        if file_writer:
            file_writer.close()
        await websocket.close()

# create an api to call llm model
@app.post("/ai_chat")
async def ai_chat(user_query: str):
    """Process a command using the LLM and return the structured data."""
    try:
        return process_user_input(user_query)
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Add a route to check server status
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)