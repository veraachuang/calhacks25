import React, { useState, useEffect } from 'react';
import webrtcService from '../services/webrtcService';
import socketService from '../services/socketService';

export default function DebugWebRTC() {
  const [status, setStatus] = useState({});
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${msg}`]);
  };

  const checkStatus = () => {
    const socket = socketService.getSocket();
    const newStatus = {
      socketConnected: socket?.connected || false,
      socketId: socket?.id || 'N/A',
      remoteId: webrtcService.remoteId || 'N/A',
      hasLocalStream: !!webrtcService.localStream,
      localTracks: webrtcService.localStream?.getTracks().map(t => `${t.kind}: ${t.enabled}`) || [],
      hasPeerConnection: !!webrtcService.peerConnection,
      peerConnectionState: webrtcService.peerConnection?.connectionState || 'N/A',
      hasRemoteStream: !!webrtcService.remoteStream,
      remoteTracks: webrtcService.remoteStream?.getTracks().map(t => `${t.kind}: ${t.enabled}`) || [],
    };
    setStatus(newStatus);
    addLog('Status checked');
  };

  const forceCall = async () => {
    addLog('🔧 Force initiating call...');
    if (!webrtcService.remoteId) {
      addLog('❌ No remote ID set!');
      return;
    }
    if (!webrtcService.localStream) {
      addLog('❌ No local stream!');
      return;
    }
    try {
      await webrtcService.startCall();
      addLog('✅ Call initiated');
    } catch (error) {
      addLog('❌ Error: ' + error.message);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-6">🔍 WebRTC Debug</h1>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <button
          onClick={checkStatus}
          className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded"
        >
          🔄 Refresh Status
        </button>
        <button
          onClick={forceCall}
          className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded"
        >
          📞 Force Call
        </button>
      </div>

      <div className="bg-gray-800 p-4 rounded mb-6">
        <h2 className="text-xl font-bold mb-2">Status</h2>
        <pre className="text-sm">{JSON.stringify(status, null, 2)}</pre>
      </div>

      <div className="bg-black p-4 rounded">
        <h2 className="text-xl font-bold mb-2">Logs</h2>
        <div className="space-y-1 max-h-96 overflow-y-auto">
          {logs.map((log, i) => (
            <div key={i} className="text-sm font-mono">{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

