import { useEffect, useState, useRef } from 'react';
import axios from 'axios';

export default function ChatDashboard() {
  const [conversations, setConversations] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const token = localStorage.getItem('token');

  // Fetch all conversations on load
  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const res = await axios.get('http://localhost:8000/auth/conversations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConversations(res.data);
    } catch (err) {
      console.error('Failed to fetch conversations', err);
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const res = await axios.get(`http://localhost:8000/auth/conversations/${conversationId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(res.data);
    } catch (err) {
      console.error('Failed to fetch messages', err);
    }
  };

  const handleSelectChat = (chat) => {
    setSelectedChat(chat);
    fetchMessages(chat.id);
  };

  const handleNewChat = async () => {
    try {
      const res = await axios.post(
        'http://localhost:8000/auth/conversations',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchConversations(); // refresh sidebar
      handleSelectChat(res.data); // auto-open new chat
    } catch (err) {
      console.error('Failed to create new chat', err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedChat) return;

    const userMsg = { sender: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(
        'http://localhost:8000/auth/messages',
        {
          conversation_id: selectedChat.id,
          content: input,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setMessages(prev => [...prev, res.data]);
    } catch (err) {
      console.error('Failed to send message', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-dashboard">
      <style>{`
        .chat-dashboard {
          display: flex;
          height: 100vh;
          font-family: sans-serif;
        }

        .sidebar {
          width: 280px;
          background: #1e3a8a;
          color: white;
          padding: 20px;
          overflow-y: auto;
        }

        .sidebar h3 {
          margin-bottom: 12px;
        }

        .new-chat-btn {
          width: 100%;
          margin-bottom: 20px;
          background: transparent;
          color: white;
          border: 2px solid white;
          padding: 10px;
          border-radius: 8px;
          cursor: pointer;
          font-weight: bold;
        }

        .chat-link {
          display: block;
          width: 100%;
          padding: 10px 12px;
          margin-bottom: 8px;
          background: white;
          color: #1e3a8a;
          border: none;
          border-radius: 6px;
          text-align: left;
          cursor: pointer;
        }

        .chat-link:hover {
          background: #e0e7ff;
        }

        .chat-link.active {
          background-color: #c7d2fe;
          font-weight: bold;
        }

        .chat-panel {
          flex: 1;
          background: #f3f4f6;
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .messages {
          flex: 1;
          padding: 20px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 60px;
        }

        .message {
          max-width: 65%;
          padding: 12px 16px;
          border-radius: 20px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }

        .user {
          align-self: flex-end;
          background: #1d4ed8;
          color: white;
        }

        .bot {
          align-self: flex-start;
          background: white;
          color: #1f2937;
        }

        .input-bar {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          padding: 10px 20px;
          display: flex;
          gap: 10px;
          background: #f3f4f6;
        }

        .input-box {
          flex: 1;
          padding: 14px;
          border-radius: 30px;
          border: 1px solid #ccc;
        }

        .send-btn {
          padding: 14px 24px;
          border-radius: 30px;
          background: #1e3a8a;
          color: white;
          font-weight: bold;
          border: none;
          cursor: pointer;
        }

        .send-btn:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
      `}</style>

      {/* Sidebar */}
      <div className="sidebar">
        <h3>Chats</h3>
        <button className="new-chat-btn" onClick={handleNewChat}>
          + New Chat
        </button>
        {conversations.map(chat => (
          <button
            key={chat.id}
            onClick={() => handleSelectChat(chat)}
            className={`chat-link ${selectedChat?.id === chat.id ? 'active' : ''}`}
          >
            Chat #{chat.id}
          </button>
        ))}
      </div>

      {/* Chat Panel */}
      <div className="chat-panel">
        <div className="messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.sender === 'user' ? 'user' : 'bot'}`}>
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="message bot">
              Mindora is typing...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {selectedChat && (
          <div className="input-bar">
            <input
              className="input-box"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
