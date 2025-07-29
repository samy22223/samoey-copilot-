const WebSocket = require('ws');
const http = require('http');

// Create HTTP server
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('WebSocket Server\n');
});

// Create WebSocket server
const wss = new WebSocket.Server({ server, path: '/ws' });

// Track connected clients
const clients = new Set();

wss.on('connection', (ws) => {
  console.log('New client connected');
  clients.add(ws);

  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connection',
    status: 'connected',
    timestamp: new Date().toISOString(),
    clientCount: clients.size
  }));

  // Broadcast to all clients when a new client connects
  broadcast({
    type: 'notification',
    message: 'A new client has connected',
    clientCount: clients.size,
    timestamp: new Date().toISOString()
  });

  // Handle messages from client
  ws.on('message', (message) => {
    console.log('Received:', message.toString());
    
    // Echo the message back to the client
    try {
      const data = JSON.parse(message);
      ws.send(JSON.stringify({
        ...data,
        echoed: true,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error parsing message:', error);
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Invalid message format',
        error: error.message,
        timestamp: new Date().toISOString()
      }));
    }
  });

  // Handle client disconnection
  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);
    
    // Notify remaining clients
    broadcast({
      type: 'notification',
      message: 'A client has disconnected',
      clientCount: clients.size,
      timestamp: new Date().toISOString()
    });
  });

  // Handle errors
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Broadcast to all connected clients
function broadcast(data) {
  const message = JSON.stringify(data);
  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

// Start the server
const PORT = process.env.PORT || 8000;
server.listen(PORT, () => {
  console.log(`WebSocket server running on ws://localhost:${PORT}/ws`);
});
// Add graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down server...');
  // Close all WebSocket connections
  clients.forEach(client => client.close());
  wss.close(() => {
    server.close(() => {
      console.log('Server has been shut down');
      process.exit(0);
    });
  });
});
