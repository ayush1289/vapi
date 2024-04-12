from enum import Enum
from vapi_python import Vapi
from fastapi import FastAPI,WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.websockets import WebSocketDisconnect,WebSocketState
import logging
import uuid




app = FastAPI()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")


@app.get("/",response_class=HTMLResponse)
def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

vapi_user = {}




class WebSocketState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"

async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """
    WebSocket endpoint function that handles incoming audio data from a frontend client.
    :param websocket: The WebSocket object representing the connection with the client.
    :param session_id: An optional session ID parameter.
    """
    await websocket.accept()
    try:
        while websocket.client_state != WebSocketState.DISCONNECTED:
            if session_id not in vapi_user:
                start_vapi(session_id)
            # Receive audio data from the client
            data = await websocket.receive_bytes()
            # Process the audio data
            response = process_audio_data(data)
            # Send the processed data back to the client
            await websocket.send_bytes(response)
    except WebSocketDisconnect:
        logging.info("WebSocket connection has been disconnected.")
        try:
            start_vapi(session_id)
            logging.info("Vapi started again.")
        except Exception as e:
            logging.error(f"An error occurred in starting again: {e}")
    except Exception as e:
        logging.error(f"An error occurred in connecting websocket: {e}")

@app.websocket("/ws/{session_id}")
def start_vapi(session_id: str) -> str:
    """
    Function to initialize a new Vapi instance and start a Vapi call for a given session ID.
    :param session_id: The session ID.
    :return: The response indicating that the Vapi call has been started.
    """
    if session_id not in vapi_user:
        vapi_user[session_id] = Vapi(api_key=api_key)
        vapi_user[session_id].start(assistant_id=assistant_id)
        logging.info(f"Vapi started for session ID: {session_id}")
    else:
        logging.info(f"Vapi already started for session ID: {session_id}")
    return "START"
@app.websocket("/ws/{session_id}")
async def stop_vapi(session_id: str):
    """
    Function to stop the Vapi instance.
    :param session_id: The session ID.
    """
    if session_id in vapi_user:
        vapi_instance = vapi_user[session_id]
        vapi_instance.stop()
        del vapi_user[session_id]
        logging.info(f"Vapi stopped for session ID: {session_id}")
    else:
        logging.info(f"No Vapi instance found for session ID: {session_id}")
    return "STOP"

def process_audio_data(data: bytes) -> str:
    """
    Function to process audio data.
    :param data: The audio data.
    :return: The processed data.
    """
    # Process audio data
    return data.decode()
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
