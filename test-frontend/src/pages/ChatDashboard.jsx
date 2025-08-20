import { useEffect, useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { sendMessage, deleteChat } from '../api/api';
import { FiSend, FiTrash2 } from 'react-icons/fi';

export default function ChatDashboard() {
  const [conversations, setConversations] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const token = localStorage.getItem('token') ?? '';

  const handleError = (err, fallbackMessage) => {
    console.error(fallbackMessage, err);
    if (err.response?.status === 401) {
      alert("Session expired. Please log in again.");
    }
  };

  const fetchConversations = useCallback(async () => {
    try {
      const res = await axios.get('http://localhost:8000/auth/conversations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConversations(res.data);
      if (res.data.length && !selectedChat) {
        setSelectedChat(res.data[0]);
      }
    } catch (err) {
      handleError(err, 'Failed to fetch conversations');
    }
  }, [token, selectedChat]);

  const fetchMessages = useCallback(async (conversationId) => {
    if (!conversationId) return;
    try {
      const res = await axios.get(
        `http://localhost:8000/auth/conversations/${conversationId}/messages`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages(res.data);
    } catch (err) {
      handleError(err, 'Failed to fetch messages');
    }
  }, [token]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    if (selectedChat) {
      fetchMessages(selectedChat.id);
    } else {
      setMessages([]);
    }
  }, [fetchMessages, selectedChat]);

  const handleSelectChat = (chat) => {
    setSelectedChat(chat);
  };

  const handleNewChat = async () => {
    try {
      const res = await axios.post(
        'http://localhost:8000/auth/conversations',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchConversations();
      setSelectedChat({ id: res.data.id, started_at: res.data.started_at });
    } catch (err) {
      handleError(err, 'Failed to create new chat');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedChat) return;
    setLoading(true);
    try {
      await sendMessage(selectedChat.id, input);
      setInput('');
      await fetchMessages(selectedChat.id);
      await fetchConversations();
    } catch (err) {
      handleError(err, 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const handleInputKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading && input.trim()) handleSend();
    }
  };

  const handleDeleteChat = async (id) => {
    if (!window.confirm("Are you sure you want to delete this conversation?")) return;
    try {
      await deleteChat(id);
      setConversations(prev => prev.filter(chat => chat.id !== id));
      if (selectedChat?.id === id) {
        setSelectedChat(null);
        setMessages([]);
      }
    } catch (err) {
      handleError(err, 'Failed to delete chat');
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatRwandaTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-GB', {
      timeZone: 'Africa/Kigali',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getChatPreviewLabel = (chat) => {
    const firstMessage =
      Array.isArray(chat.messages) && chat.messages.length
        ? chat.messages.find(m => m.sender === 'user')?.content
        : null;

    if (firstMessage) {
      return firstMessage.length > 25
        ? firstMessage.slice(0, 25) + '...'
        : firstMessage;
    }

    return `Started on ${new Date(chat.started_at).toLocaleDateString('en-GB', {
      timeZone: 'Africa/Kigali'
    })}`;
  };

  return (
    <div className="chat-dashboard">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
        .chat-dashboard {
          display: flex;
          height: 100vh;
          font-family: 'Poppins', sans-serif;
          background: #fefaf6;
        }
        .sidebar {
          width: 280px;
          background: linear-gradient(to bottom, #d946ef, #9333ea);
          color: white;
          padding: 24px 18px;
          overflow-y: auto;
          box-shadow: 2px 0 10px rgba(0, 0, 0, 0.08);
        }
        .sidebar h3 {
          font-size: 22px;
          font-weight: 600;
          margin-bottom: 20px;
        }
        .new-chat-btn {
          width: 100%;
          padding: 12px;
          background: white;
          color: #9333ea;
          font-weight: bold;
          border: none;
          border-radius: 10px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          margin-bottom: 20px;
          cursor: pointer;
        }
        .chat-item {
          display: flex;
          align-items: center;
          background: #f3e8ff;
          border-radius: 12px;
          margin-bottom: 10px;
          padding-left: 6px;
        }
        .chat-item.active {
          background-color: #e9d5ff;
        }
        .chat-link {
          flex: 1;
          background: transparent;
          border: none;
          padding: 14px;
          text-align: left;
          font-weight: 500;
          color: #4b0082;
          cursor: pointer;
        }
        .delete-btn {
          background: transparent;
          border: none;
          cursor: pointer;
          padding: 4px;
        }
        .delete-btn svg {
          color: #ff6b6b; /* default light red */
          transition: color 0.2s ease;
        }
        .delete-btn:hover svg {
          color: #ff4d4d; /* darker red on hover */
        }
        .chat-panel {
          flex: 1;
          display: flex;
          flex-direction: column;
          position: relative;
          background: #fefaf6;
        }
        .messages {
          flex: 1;
          padding: 30px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .message {
          max-width: 60%;
          padding: 16px 20px;
          border-radius: 14px;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
          font-size: 15px;
          background: white;
          position: relative;
        }
        .user {
          align-self: flex-end;
          background: linear-gradient(to right, #a855f7, #9333ea);
          color: white;
        }
        .bot {
          align-self: flex-start;
          background: #fff;
          color: #1f2937;
        }
        .timestamp {
          font-size: 12px;
          margin-top: 6px;
          color: #6b7280;
        }
        .emotion {
          font-size: 12px;
          margin-top: 4px;
          color: #6b7280;
          display: flex;
          align-items: center;
        }
        .emotion-dot {
          width: 8px;
          height: 8px;
          background-color: green;
          border-radius: 50%;
          margin-right: 6px;
        }
        .input-bar {
          position: sticky;
          bottom: 0;
          padding: 12px 20px;
          display: flex;
          align-items: center;
          background: white;
          border-top: 1px solid #ddd;
        }
        .input-box {
          flex: 1;
          padding: 14px 18px;
          border-radius: 30px;
          border: 1px solid #ccc;
          font-size: 15px;
          background: #fdf6f0;
        }
        .send-btn {
          margin-left: 10px;
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: linear-gradient(to right, #ec4899, #8b5cf6);
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }
        .send-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .send-btn svg {
          width: 22px;
          height: 22px;
          fill: white;
        }
      `}</style>

      <div className="sidebar">
        <h3>MINDORA CHAT 💬</h3>
        <button className="new-chat-btn" onClick={handleNewChat}>+ New Chat</button>
        {conversations.map(chat => (
          <div
            key={chat.id}
            className={`chat-item ${selectedChat?.id === chat.id ? 'active' : ''}`}
          >
            <button
              onClick={() => handleSelectChat(chat)}
              className="chat-link"
            >
              {getChatPreviewLabel(chat)}
            </button>
            <button
              className="delete-btn"
              onClick={() => handleDeleteChat(chat.id)}
              title="Delete chat"
            >
              <FiTrash2 size={18} />
            </button>
          </div>
        ))}
      </div>

      <div className="chat-panel">
        <div className="messages">
          {messages.length === 0 && !loading && (
            <div style={{ color: '#777', textAlign: 'center', marginTop: '50px' }}>
              Start the conversation
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.sender === 'user' ? 'user' : 'bot'}`}>
              <div style={{ whiteSpace: 'pre-line' }}>{msg.content}</div>
              {msg.sender === 'bot' && msg.emotion && (
                <div className="emotion">
                  <span className="emotion-dot"></span> Emotion: <strong>{msg.emotion}</strong>
                </div>
              )}
              <div className="timestamp">
                {formatRwandaTime(msg.timestamp)}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message bot">Mindora is typing...</div>
          )}
          <div ref={messagesEndRef} />
        </div>
        {selectedChat && (
          <div className="input-bar">
            <input
              className="input-box"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Type your message..."
              disabled={loading}
              aria-label="Message input"
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              aria-label="Send message"
            >
              <FiSend size={20} color="#fff" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}