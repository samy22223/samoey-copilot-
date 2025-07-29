import os
import asyncio
import json
import logging
import platform
import signal
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import etcd3

# Import AI Chat Manager
from ai_chat import AIChatManager

# Import WebSocket manager
from websocket_manager import websocket_endpoint, manager as ws_manager

# Import Code GPT integration
from codegpt_integration import CodeGPTRequest, codegpt_integration

# Import key-value store
from kv_store import KeyValueStore

# Initialize key-value store
kv_store = KeyValueStore()

# Initialize AI Chat Manager
chat_manager = AIChatManager()

# Templates
templates = Jinja2Templates(directory="templates")

# Setup
app = FastAPI(title="Pinnacle Copilot",
              description="AI-powered system monitoring and assistant",
              version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Xline client
xline_client = None

# Initialize chat manager
chat_manager = get_chat_manager()

# Initialize Xline process
xline_process = None

def get_xline_client():
    """Dependency to get Xline client instance."""
    global xline_client, xline_process
    if xline_client is None:
        # Start Xline server
        xline_process = subprocess.Popen(
            ["/Users/samoey/Desktop/Xline/target/release/xline", 
             "--config", 
             "/Users/samoey/Desktop/Xline/config.toml"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Give it a moment to start
        import time
        time.sleep(2)
        
        # Initialize client
        xline_client = PinnacleXlineClient()
    return xline_client

# Models
class ChatMessage(BaseModel):
    message: str
    language: str = "en"
    user_id: Optional[str] = None

# Ensure directories exist
Path("templates").mkdir(exist_ok=True)
Path("static/css").mkdir(exist_ok=True)
Path("static/js").mkdir(exist_ok=True)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

# System monitoring
async def monitor_system():
    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "type": "system_metrics",
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }
            
            await manager.broadcast(metrics)
            
        except Exception as e:
            print(f"Error in system monitoring: {e}")
        
        await asyncio.sleep(2)

# API Endpoints
# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication
    
    Message types:
    - chat: Send and receive chat messages
    - system_metrics: Get system metrics
    - subscribe: Subscribe to real-time updates
    """
    await websocket.accept()
    client_id = str(uuid.uuid4())
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Client state
        subscribed_to = set()
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "chat":
                # Handle chat message
                conversation_id = data.get("conversation_id") or str(uuid.uuid4())
                user_message = data.get("message", "")
                user_id = data.get("user_id", "anonymous")
                
                if not user_message:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Message cannot be empty",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                # Log the user message in the key-value store
                message_id = str(uuid.uuid4())
                kv_store.put(f"chat/{conversation_id}/{message_id}", {
                    "role": "user",
                    "content": user_message,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Get conversation history for context
                messages = []
                for key in kv_store.list_keys(f"chat/{conversation_id}/"):
                    message = kv_store.get(key)
                    if message and message.get("content"):
                        messages.append({
                            "role": message.get("role", "user"),
                            "content": message.get("content", ""),
                            "timestamp": message.get("timestamp")
                        })
                
                # Sort messages by timestamp
                messages.sort(key=lambda x: x.get("timestamp", ""))
                
                # Generate response using the chat manager
                chat_history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
                response = await chat_manager.generate_response(
                    messages=chat_history,
                    conversation_id=conversation_id
                )
                
                # Log the AI response in the key-value store
                response_id = str(uuid.uuid4())
                kv_store.put(f"chat/{conversation_id}/{response_id}", {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Send the response back to the client
                await websocket.send_json({
                    "type": "chat_response",
                    "response": response,
                    "conversation_id": conversation_id,
                    "message_id": response_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "system_metrics":
                # Send current system metrics
                await websocket.send_json({
                    "type": "system_metrics",
                    "metrics": {
                        "cpu_percent": psutil.cpu_percent(),
                        "memory_percent": psutil.virtual_memory().percent,
                        "disk_percent": psutil.disk_usage('/').percent,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
            elif message_type == "subscribe":
                # Subscribe to real-time updates
                channels = data.get("channels", [])
                if not isinstance(channels, list):
                    channels = [channels]
                
                subscribed_to.update(channels)
                await websocket.send_json({
                    "type": "subscription_updated",
                    "subscribed_to": list(subscribed_to),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif message_type == "unsubscribe":
                # Unsubscribe from channels
                channels = data.get("channels", [])
                if not isinstance(channels, list):
                    channels = [channels]
                
                subscribed_to.difference_update(channels)
                await websocket.send_json({
                    "type": "subscription_updated",
                    "subscribed_to": list(subscribed_to),
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        logging.info(f"Client {client_id} disconnected")
        
    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "error": "Invalid JSON message",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        error_id = str(uuid.uuid4())
        logging.error(f"WebSocket error [{error_id}]: {str(e)}", exc_info=True)
        
        try:
            await websocket.send_json({
                "type": "error",
                "error": "An unexpected error occurred",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass  # Client may have disconnected
            
        # Log the error to our key-value store
        kv_store.put(f"errors/websocket/{error_id}", {
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "error": str(e),
            "subscribed_to": list(subscribed_to) if 'subscribed_to' in locals() else []
        })

# API Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint that verifies the key-value store is operational."""
    test_key = f"health_check_{int(time.time())}"
    test_value = {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    
    try:
        # Test key-value store write
        if not kv_store.put(test_key, test_value):
            raise RuntimeError("Failed to write to key-value store")
        
        # Test key-value store read
        result = kv_store.get(test_key)
        
        # Clean up
        kv_store.delete(test_key)
        
        if result == test_value:
            return {
                "status": "healthy",
                "kv_store": "operational",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "kv_store": "read_write_mismatch",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "kv_store": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/codegpt")
async def codegpt_endpoint(request: CodeGPTRequest):
    """Endpoint for Code GPT integration."""
    request_id = str(uuid.uuid4())
    request_data = request.dict()
    
    try:
        # Store the request in the key-value store for context
        kv_store.put(f"codegpt/requests/{request_id}", {
            "timestamp": datetime.utcnow().isoformat(),
            **request_data
        })
        
        # Process the request
        response = await codegpt_integration.process_request(chat_manager, request)
        
        # Store the response if successful
        if response.get('success'):
            kv_store.put(f"codegpt/responses/{request_id}", {
                "timestamp": datetime.utcnow().isoformat(),
                "response": response
            })
        
        return response
        
    except Exception as e:
        # Log the error
        kv_store.put(f"codegpt/errors/{request_id}", {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "request": request_data
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to process Code GPT request",
                "request_id": request_id
            }
        )

@app.post("/api/chat")
async def chat_endpoint(request: Dict[str, Any]):
    """Handle chat messages and return AI responses.
    
    Request format:
    {
        "message": "User's message",
        "conversation_id": "optional-conversation-id"
    }
    """
    try:
        # Get or create conversation ID
        conversation_id = request.get("conversation_id") or str(uuid.uuid4())
        user_message = request.get("message", "")
        user_id = request.get("user_id", "anonymous")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Log the user message in the key-value store
        message_id = str(uuid.uuid4())
        kv_store.put(f"chat/{conversation_id}/{message_id}", {
            "role": "user",
            "content": user_message,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Get conversation history
        messages = []
        for key in kv_store.list_keys(f"chat/{conversation_id}/"):
            message = kv_store.get(key)
            if message:
                messages.append({
                    "role": message.get("role", "user"),
                    "content": message.get("content", ""),
                    "timestamp": message.get("timestamp")
                })
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        # Generate response using the chat manager
        chat_history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        response = await chat_manager.generate_response(
            messages=chat_history,
            conversation_id=conversation_id
        )
        
        # Log the AI response in the key-value store
        response_id = str(uuid.uuid4())
        kv_store.put(f"chat/{conversation_id}/{response_id}", {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "response": response,
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_id = str(uuid.uuid4())
        kv_store.put(f"errors/chat/{error_id}", {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "request": request
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to process chat message",
                "error_id": error_id
            }
        )

@app.get("/api/chat/history")
async def get_history(conversation_id: Optional[str] = None, limit: int = 10):
    """Get chat history from the key-value store.
    
    Args:
        conversation_id: Optional conversation ID to filter by.
        limit: Maximum number of messages to return per conversation.
        
    Returns:
        A dictionary containing the chat history.
    """
    try:
        if conversation_id:
            # Get messages for a specific conversation
            messages = []
            for key in kv_store.list_keys(f"chat/{conversation_id}/"):
                message = kv_store.get(key)
                if message:
                    messages.append({
                        "id": key.split('/')[-1],
                        "conversation_id": conversation_id,
                        "role": message.get("role", "user"),
                        "content": message.get("content", ""),
                        "timestamp": message.get("timestamp"),
                        "user_id": message.get("user_id", "anonymous")
                    })
            
            # Sort by timestamp and apply limit
            messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return {"conversations": [{
                "id": conversation_id,
                "messages": messages[:limit]
            }]}
        else:
            # Get all conversations
            conversations = {}
            for key in kv_store.list_keys("chat/"):
                if key.count('/') >= 2:  # Ensure it's a message key
                    parts = key.split('/')
                    if len(parts) >= 3:
                        conv_id = parts[1]
                        if conv_id not in conversations:
                            conversations[conv_id] = []
                        
                        message = kv_store.get(key)
                        if message:
                            conversations[conv_id].append({
                                "id": parts[-1],
                                "role": message.get("role", "user"),
                                "content": message.get("content", ""),
                                "timestamp": message.get("timestamp"),
                                "user_id": message.get("user_id", "anonymous")
                            })
            
            # Sort each conversation's messages and apply limit
            result = []
            for conv_id, messages in conversations.items():
                messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                result.append({
                    "id": conv_id,
                    "last_message": messages[0] if messages else None,
                    "message_count": len(messages),
                    "messages": messages[:limit]
                })
            
            # Sort conversations by most recent message
            result.sort(key=lambda x: x["last_message"]["timestamp"] if x["last_message"] else "", reverse=True)
            return {"conversations": result}
            
    except Exception as e:
        error_id = str(uuid.uuid4())
        kv_store.put(f"errors/history/{error_id}", {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "conversation_id": conversation_id
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to retrieve chat history",
                "error_id": error_id
            }
        )

# System Info Endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_count": psutil.cpu_count(),
        "memory": {"total": psutil.virtual_memory().total},
        "disk_usage": psutil.disk_usage('/')._asdict(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "total_memory": psutil.virtual_memory().total
    })

@app.get("/api/system/info")
async def get_system_info():
    """Get system information"""
    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_count": psutil.cpu_count(),
        "memory": {"total": psutil.virtual_memory().total},
        "disk_usage": psutil.disk_usage('/')._asdict(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "total_memory": psutil.virtual_memory().total
    }

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Create default template if it doesn't exist
if not os.path.exists("templates/index.html"):
    with open("templates/index.html", "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pinnacle Copilot</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                .status-card { transition: all 0.3s ease; }
                .status-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
            </style>
        </head>
        <body class="bg-gray-100">
            <div class="min-h-screen">
                <nav class="bg-blue-600 text-white p-4 shadow-lg">
                    <div class="container mx-auto flex justify-between items-center">
                        <h1 class="text-2xl font-bold">Pinnacle Copilot</h1>
                        <div class="flex items-center space-x-4">
                            <span id="status-indicator" class="h-3 w-3 rounded-full bg-yellow-400 animate-pulse"></span>
                            <span id="status-text" class="text-sm">Connecting...</span>
                        </div>
                    </div>
                </nav>
                
                <main class="container mx-auto p-4 md:p-8">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <!-- CPU Card -->
                        <div class="bg-white rounded-lg shadow p-6 status-card">
                            <h2 class="text-xl font-semibold mb-4 text-gray-800">CPU Usage</h2>
                            <div class="h-4 bg-gray-200 rounded-full mb-2">
                                <div id="cpu-bar" class="h-full bg-blue-500 rounded-full" style="width: 0%"></div>
                            </div>
                            <p id="cpu-text" class="text-right font-mono">0%</p>
                            <div class="mt-4">
                                <p class="text-sm text-gray-600">Cores: <span id="cpu-cores" class="font-mono">0</span></p>
                            </div>
                        </div>
                        
                        <!-- Memory Card -->
                        <div class="bg-white rounded-lg shadow p-6 status-card">
                            <h2 class="text-xl font-semibold mb-4 text-gray-800">Memory</h2>
                            <div class="h-4 bg-gray-200 rounded-full mb-2">
                                <div id="mem-bar" class="h-full bg-green-500 rounded-full" style="width: 0%"></div>
                            </div>
                            <p id="mem-text" class="text-right font-mono">0% (0 GB / 0 GB)</p>
                            <div class="mt-4">
                                <p class="text-sm text-gray-600">Available: <span id="mem-available" class="font-mono">0 GB</span></p>
                            </div>
                        </div>
                        
                        <!-- Disk Card -->
                        <div class="bg-white rounded-lg shadow p-6 status-card">
                            <h2 class="text-xl font-semibold mb-4 text-gray-800">Disk Usage</h2>
                            <div class="h-4 bg-gray-200 rounded-full mb-2">
                                <div id="disk-bar" class="h-full bg-yellow-500 rounded-full" style="width: 0%"></div>
                            </div>
                            <p id="disk-text" class="text-right font-mono">0% (0 GB / 0 GB)</p>
                            <div class="mt-4">
                                <p class="text-sm text-gray-600">Free: <span id="disk-free" class="font-mono">0 GB</span></p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- System Info -->
                    <div class="mt-8 bg-white rounded-lg shadow p-6">
                        <h2 class="text-xl font-semibold mb-4 text-gray-800">System Information</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                            <div><span class="text-gray-600">Hostname:</span> <span id="hostname" class="font-mono">Loading...</span></div>
                            <div><span class="text-gray-600">OS:</span> <span id="os" class="font-mono">Loading...</span></div>
                            <div><span class="text-gray-600">Python:</span> <span id="python-version" class="font-mono">Loading...</span></div>
                            <div><span class="text-gray-600">CPU Cores:</span> <span id="cpu-cores" class="font-mono">0</span></div>
                            <div><span class="text-gray-600">Total Memory:</span> <span id="total-memory" class="font-mono">0 GB</span></div>
                            <div><span class="text-gray-600">Uptime:</span> <span id="uptime" class="font-mono">0h 0m</span></div>
                        </div>
                    </div>
                    
                    <!-- CPU Usage Chart -->
                    <div class="mt-8 bg-white rounded-lg shadow p-6">
                        <h2 class="text-xl font-semibold mb-4 text-gray-800">CPU Usage History</h2>
                        <canvas id="cpu-chart" height="100"></canvas>
                    </div>
                </main>
            </div>
            
            <script>
                // System info
                fetch('/api/system/info')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('hostname').textContent = data.hostname;
                        document.getElementById('os').textContent = data.os;
                        document.getElementById('python-version').textContent = data.python_version;
                        document.getElementById('cpu-cores').textContent = data.cpu_cores;
                        document.getElementById('total-memory').textContent = 
                            (data.total_memory / (1024 ** 3)).toFixed(1) + ' GB';
                    });
                
                // WebSocket connection
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
                
                // Chart setup
                const cpuCtx = document.getElementById('cpu-chart').getContext('2d');
                const cpuChart = new Chart(cpuCtx, {
                    type: 'line',
                    data: {
                        labels: Array(30).fill(''),
                        datasets: [{
                            label: 'CPU Usage %',
                            data: [],
                            borderColor: 'rgb(59, 130, 246)',
                            tension: 0.1,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        },
                        animation: false
                    }
                });
                
                // Update chart
                function updateChart(value) {
                    const chart = cpuChart.data.datasets[0].data;
                    chart.push(value);
                    if (chart.length > 30) chart.shift();
                    cpuChart.update('none');
                }
                
                // WebSocket message handler
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'system_metrics') {
                        // Update status
                        document.getElementById('status-indicator').className = 'h-3 w-3 rounded-full bg-green-500';
                        document.getElementById('status-text').textContent = 'Connected';
                        
                        // Update CPU
                        const cpuPercent = Math.round(data.cpu_percent);
                        document.getElementById('cpu-bar').style.width = `${cpuPercent}%`;
                        document.getElementById('cpu-text').textContent = `${cpuPercent}%`;
                        updateChart(cpuPercent);
                        
                        // Update Memory
                        const mem = data.memory;
                        const memPercent = Math.round(mem.percent);
                        const usedGB = (mem.used / (1024 ** 3)).toFixed(1);
                        const totalGB = (mem.total / (1024 ** 3)).toFixed(1);
                        const availGB = (mem.available / (1024 ** 3)).toFixed(1);
                        
                        document.getElementById('mem-bar').style.width = `${memPercent}%`;
                        document.getElementById('mem-text').textContent = 
                            `${memPercent}% (${usedGB} GB / ${totalGB} GB)`;
                        document.getElementById('mem-available').textContent = 
                            `${availGB} GB`;
                        
                        // Update Disk
                        const disk = data.disk;
                        const diskPercent = Math.round(disk.percent);
                        const usedDiskGB = (disk.used / (1024 ** 3)).toFixed(1);
                        const totalDiskGB = (disk.total / (1024 ** 3)).toFixed(1);
                        const freeDiskGB = (disk.free / (1024 ** 3)).toFixed(1);
                        
                        document.getElementById('disk-bar').style.width = `${diskPercent}%`;
                        document.getElementById('disk-text').textContent = 
                            `${diskPercent}% (${usedDiskGB} GB / ${totalDiskGB} GB)`;
                        document.getElementById('disk-free').textContent = 
                            `${freeDiskGB} GB`;
                        
                        // Update uptime
                        const uptime = new Date() - new Date(data.timestamp);
                        const hours = Math.floor(uptime / 3600000);
                        const minutes = Math.floor((uptime % 3600000) / 60000);
                        document.getElementById('uptime').textContent = 
                            `${hours}h ${minutes}m`;
                    }
                };
                
                // Handle connection errors
                ws.onclose = function() {
                    document.getElementById('status-indicator').className = 'h-3 w-3 rounded-full bg-red-500';
                    document.getElementById('status-text').textContent = 'Disconnected';
                    
                    // Try to reconnect after 5 seconds
                    setTimeout(() => window.location.reload(), 5000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    document.getElementById('status-indicator').className = 'h-3 w-3 rounded-full bg-yellow-500';
                    document.getElementById('status-text').textContent = 'Connection error';
                };
            </script>
        </body>
        </html>
        """)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Close any open connections
        if hasattr(kv_store, 'client'):
            kv_store.client.close()
            
        logging.info("Pinnacle Copilot shutdown complete")
    except Exception as e:
        logging.error(f"Error during shutdown: {str(e)}")

# Start system monitoring when the app starts
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    try:
        # Test the key-value store connection
        test_key = "pinnacle:startup_test"
        test_value = {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
        
        if not kv_store.put(test_key, test_value):
            logging.error("Failed to write to key-value store")
            raise RuntimeError("Failed to initialize key-value store")
            
        if kv_store.get(test_key) != test_value:
            logging.error("Failed to read from key-value store")
            raise RuntimeError("Failed to verify key-value store integrity")
            
        # Clean up test key
        kv_store.delete(test_key)
        
        logging.info("Pinnacle Copilot started successfully with key-value store")
        
    except Exception as e:
        logging.error(f"Startup error: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    
    def open_browser():
        # Wait for server to start
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8000")
    
    # Start the browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the server
    uvicorn.run(
        "pinnacle_copilot:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
