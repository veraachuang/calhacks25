import React, { useState, useEffect } from 'react';
import socketService from '../services/socketService';
import apiService from '../services/apiService';

export default function DebugConnection() {
  const [logs, setLogs] = useState([]);
  const [isConnecting, setIsConnecting] = useState(false);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
    console.log(`[${type.toUpperCase()}] ${message}`);
  };

  const testConnection = async () => {
    setIsConnecting(true);
    setLogs([]);
    
    try {
      // Step 1: Check backend URL
      const backendUrl = import.meta.env.VITE_BACKEND_URL || `https://${window.location.hostname}:8765`;
      addLog(`🔗 Backend URL: ${backendUrl}`, 'info');
      
      // Step 2: Try to connect socket
      addLog('🔌 Attempting socket connection...', 'info');
      const socket = socketService.connect();
      
      // Step 3: Wait for connection
      await new Promise((resolve, reject) => {
        if (socket.connected) {
          addLog('✅ Socket already connected!', 'success');
          resolve();
        } else {
          const timeout = setTimeout(() => {
            addLog('❌ Connection timeout (10s)', 'error');
            reject(new Error('Connection timeout'));
          }, 10000);
          
          socket.once('connect', () => {
            clearTimeout(timeout);
            addLog(`✅ Socket connected! ID: ${socket.id}`, 'success');
            resolve();
          });
          
          socket.once('connect_error', (err) => {
            clearTimeout(timeout);
            addLog(`❌ Connection error: ${err.message}`, 'error');
            reject(err);
          });
        }
      });
      
      // Step 4: Try to join room
      addLog('🚪 Joining matchmaking room...', 'info');
      socketService.joinRoom('matchmaking');
      
      // Step 5: Wait for session_info
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          addLog('❌ No session_info received (10s timeout)', 'error');
          reject(new Error('No session_info'));
        }, 10000);
        
        socket.once('session_info', (data) => {
          clearTimeout(timeout);
          addLog(`✅ Session info received: ${JSON.stringify(data)}`, 'success');
          resolve(data);
        });
        
        socket.once('session_error', (data) => {
          clearTimeout(timeout);
          addLog(`⚠️ Session error: ${data.message}`, 'warning');
          reject(new Error(data.message));
        });
      });
      
      addLog('🎉 All tests passed!', 'success');
      
    } catch (error) {
      addLog(`💥 Test failed: ${error.message}`, 'error');
    } finally {
      setIsConnecting(false);
    }
  };

  const getLogColor = (type) => {
    switch(type) {
      case 'success': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">🔍 Connection Debugger</h1>
        
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Configuration</h2>
          <div className="space-y-2 text-sm">
            <div className="flex">
              <span className="text-gray-400 w-40">VITE_BACKEND_URL:</span>
              <span className="text-white font-mono">{import.meta.env.VITE_BACKEND_URL || '(not set)'}</span>
            </div>
            <div className="flex">
              <span className="text-gray-400 w-40">Fallback URL:</span>
              <span className="text-white font-mono">{`https://${window.location.hostname}:8765`}</span>
            </div>
            <div className="flex">
              <span className="text-gray-400 w-40">Current location:</span>
              <span className="text-white font-mono">{window.location.href}</span>
            </div>
          </div>
        </div>
        
        <button
          onClick={testConnection}
          disabled={isConnecting}
          className={`w-full py-4 rounded-lg font-bold text-lg mb-6 ${
            isConnecting 
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:scale-105 transition-transform'
          }`}
        >
          {isConnecting ? '🔄 Testing...' : '▶️ Run Connection Test'}
        </button>
        
        <div className="bg-black rounded-lg p-6 font-mono text-sm">
          <h2 className="text-xl font-bold text-white mb-4">📋 Logs</h2>
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-gray-500">Click "Run Connection Test" to start...</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="flex gap-3">
                  <span className="text-gray-500">{log.timestamp}</span>
                  <span className={getLogColor(log.type)}>{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

