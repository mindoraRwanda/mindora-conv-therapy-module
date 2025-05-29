import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Optional: Add a welcome message when the component mounts
  useEffect(() => {
    setMessages([
      {
        role: 'bot',
        text: "Hello! I'm your therapy assistant. How are you feeling today?",
        timestamp: new Date()
      }
    ]);
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    
    // Add user message
    const userMessage = {
      role: 'user',
      text: inputText,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    
    try {
      // Send to API
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: inputText,
        conversation_id: conversationId
      });
      
      // Save conversation ID if this is the first message
      if (!conversationId && response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }
      
      // Add bot response
      setMessages(prev => [
        ...prev, 
        {
          role: 'bot',
          text: response.data.response,
          timestamp: new Date(response.data.timestamp)
        }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev, 
        {
          role: 'bot',
          text: 'Sorry, there was an error processing your request. Please try again later.',
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Format timestamp
  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="app-container">
      <div className="chat-header">
        <h1>Mindora Therapy Bot</h1>
        <p>Testing Interface</p>
      </div>
      
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.role === 'user' ? 'user-message' : 'bot-message'}`}
          >
            <div className="message-content">
              <p>{message.text}</p>
              <span className="timestamp">{formatTime(message.timestamp)}</span>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="loading-indicator">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form className="input-area" onSubmit={handleSend}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !inputText.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;