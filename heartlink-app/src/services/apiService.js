// Use environment variable for backend URL (ngrok tunnel) or fall back to localhost
const BACKEND_URL = `https://${window.location.hostname}:8765`;

class ApiService {
  async updateProfile(sessionId, userId, profileData) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/profile/update-bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId,
          updates: profileData
        })
      });

      if (!response.ok) {
        throw new Error(`Profile update failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error updating profile:', error);
      throw error;
    }
  }

  async getBothProfiles(sessionId) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/profile/both?session_id=${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Get profiles failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error getting profiles:', error);
      throw error;
    }
  }

  async getSession(sessionId) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/sessions/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Get session failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error getting session:', error);
      throw error;
    }
  }

  async endSession(sessionId) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/sessions/${sessionId}/end`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`End session failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error ending session:', error);
      throw error;
    }
  }
}

const apiService = new ApiService();
export default apiService;

