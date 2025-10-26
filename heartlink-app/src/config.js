/**
 * Configuration for backend connectivity
 * 
 * This allows the app to connect to different backend servers:
 * - Same device: Uses localhost
 * - Different device on same network: Uses server's local IP
 */

export const getBackendUrl = () => {
  // Priority 1: Environment variable (set via .env.local)
  if (import.meta.env.VITE_BACKEND_URL) {
    console.log('🔧 Using backend from env:', import.meta.env.VITE_BACKEND_URL);
    return import.meta.env.VITE_BACKEND_URL;
  }
  
  // Priority 2: Runtime configuration (can be set by setup script)
  if (window.HEARTLINK_BACKEND_URL) {
    console.log('🔧 Using backend from window config:', window.HEARTLINK_BACKEND_URL);
    return window.HEARTLINK_BACKEND_URL;
  }
  
  // Priority 3: Auto-detect based on current hostname
  const hostname = window.location.hostname;
  
  // If we're on localhost, connect to localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const url = 'https://localhost:8765';
    console.log('🔧 Auto-detected localhost backend:', url);
    return url;
  }
  
  // Otherwise, assume backend is on the same host as frontend
  const url = `https://${hostname}:8765`;
  console.log('🔧 Auto-detected network backend:', url);
  return url;
};

export const BACKEND_URL = getBackendUrl();

// Export for debugging
window.HEARTLINK_CONFIG = {
  backendUrl: BACKEND_URL,
  hostname: window.location.hostname,
};

console.log('🌐 HeartLink Backend Configuration:', window.HEARTLINK_CONFIG);

