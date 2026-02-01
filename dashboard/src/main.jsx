import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { WebSocketProvider } from './context/WebSocketContext.jsx'
import './index.css'

// Get token from localStorage for WebSocket connection
const token = localStorage.getItem('auth_token');

const AppWithProviders = () => (
  <AuthProvider>
    {token ? (
      <WebSocketProvider token={token}>
        <App />
      </WebSocketProvider>
    ) : (
      <App />
    )}
  </AuthProvider>
);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppWithProviders />
  </React.StrictMode>,
)
