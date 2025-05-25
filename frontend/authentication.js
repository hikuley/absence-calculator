// Authentication helper functions for the Absence Calculator

// Token management
function saveToken(token) {
  localStorage.setItem('auth_token', token);
}

function getToken() {
  return localStorage.getItem('auth_token');
}

function removeToken() {
  localStorage.removeItem('auth_token');
}

function isAuthenticated() {
  return !!getToken();
}

// API calls with authentication
async function apiCall(endpoint, options = {}) {
  const token = getToken();
  
  // Set default headers
  if (!options.headers) {
    options.headers = {};
  }
  
  // Add content type if not set and method is not GET
  if (options.method && options.method !== 'GET' && !options.headers['Content-Type']) {
    options.headers['Content-Type'] = 'application/json';
  }
  
  // Add authorization header if token exists
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }
  
  // Make the API call
  try {
    const response = await fetch(`${window.API_URL}${endpoint}`, options);
    
    // Handle unauthorized responses
    if (response.status === 401) {
      // Clear token and redirect to login
      removeToken();
      showLoginPage();
      throw new Error('Unauthorized: Please log in again');
    }
    
    return response;
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
}

// Authentication API calls
async function login(username, password) {
  try {
    const response = await fetch(`${window.API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }
    
    const data = await response.json();
    saveToken(data.access_token);
    return true;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

async function signup(username, email, password) {
  try {
    const response = await fetch(`${window.API_URL}/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, email, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
}

async function logout() {
  try {
    const token = getToken();
    if (!token) {
      // Already logged out
      return true;
    }
    
    const response = await fetch(`${window.API_URL}/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    // Remove token regardless of response
    removeToken();
    return response.ok;
  } catch (error) {
    console.error('Logout error:', error);
    // Remove token even if the API call fails
    removeToken();
    throw error;
  }
}

// User profile
async function getUserProfile() {
  try {
    const response = await apiCall('/me');
    
    if (!response.ok) {
      throw new Error('Failed to get user profile');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get user profile error:', error);
    throw error;
  }
}
