
// import { useEffect, useState, useRef, useCallback } from 'react';
// import axios from 'axios';
// import {
//   sendMessage //  make sure this is included here
// } from '../api/api';



// export default function ChatDashboard() {
//   const [conversations, setConversations] = useState([]);
//   const [selectedChat, setSelectedChat] = useState(null);
//   const [messages, setMessages] = useState([]);
//   const [input, setInput] = useState('');
//   const [loading, setLoading] = useState(false);
//   const messagesEndRef = useRef(null);
//   const token = localStorage.getItem('token') ?? '';

//   const handleError = (err, fallbackMessage) => {
//     console.error(fallbackMessage, err);
//     if (err.response?.status === 401) {
//       alert("Session expired. Please log in again.");
//     }
//   };

//   const fetchConversations = useCallback(async () => {
//     try {
//       const res = await axios.get('http://localhost:8000/auth/conversations', {
//         headers: { Authorization: `Bearer ${token}` },
//       });
//       setConversations(res.data);
//       if (res.data.length && !selectedChat) {
//         setSelectedChat(res.data[0]);
//       }
//     } catch (err) {
//       handleError(err, 'Failed to fetch conversations');
//     }
//   }, [token, selectedChat]);

//   const fetchMessages = useCallback(async (conversationId) => {
//     try {
//       const res = await axios.get(`http://localhost:8000/auth/conversations/${conversationId}/messages`, {
//         headers: { Authorization: `Bearer ${token}` },
//       });
//       setMessages(res.data);
//     } catch (err) {
//       handleError(err, 'Failed to fetch messages');
//     }
//   }, [token]);

//   useEffect(() => {
//     fetchConversations();
//   }, [fetchConversations]);

//   useEffect(() => {
//     if (selectedChat) {
//       fetchMessages(selectedChat.id);
//     }
//   }, [fetchMessages, selectedChat]);

//   const handleSelectChat = (chat) => {
//     setSelectedChat(chat);
//   };

//   const handleNewChat = async () => {
//     try {
//       const res = await axios.post(
//         'http://localhost:8000/auth/conversations',
//         {},
//         { headers: { Authorization: `Bearer ${token}` } }
//       );

//       await fetchConversations();
//       const newChat = { id: res.data.id, started_at: res.data.started_at };
//       setSelectedChat(newChat);
//     } catch (err) {
//       handleError(err, 'Failed to create new chat');
//     }
//   };

//   const handleSend = async () => {
//   if (!input.trim() || !selectedChat) return;

//   const userMsg = {
//     sender: 'user',
//     content: input,
//     timestamp: new Date().toISOString()
//   };

//   // Show user's message immediately
//   setMessages(prev => [...prev, userMsg]);
//   setInput('');
//   setLoading(true);

//   try {
//     const res = await sendMessage(selectedChat.id, input);

//     if (!res || !res.response || !res.response.content) {
//       throw new Error('Invalid bot response');
//     }

//     const botMsg = {
//       sender: 'bot',
//       content: res.response.content,
//       timestamp: res.response.timestamp || new Date().toISOString(),
//       emotion: res.emotion || null
//     };

//     // Append bot response without overwriting the message list
//     setMessages(prev => [...prev, botMsg]);

//     // Optional: Slight delay to allow DB sync before fetching full list
//     // await new Promise(resolve => setTimeout(resolve, 300));
//     // await fetchMessages(selectedChat.id); // Only if syncing is absolutely needed
//   } catch (err) {
//     handleError(err, 'Failed to send message');
//   } finally {
//     setLoading(false);
//   }
// };

//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//   }, [messages]);

//   return (
//     <div className="chat-dashboard">
//       <style>{`
//         .chat-dashboard {
//           display: flex;
//           height: 100vh;
//           font-family: sans-serif;
//         }
//         .sidebar {
//           width: 280px;
//           background: #1e3a8a;
//           color: white;
//           padding: 20px;
//           overflow-y: auto;
//         }
//         .sidebar h3 {
//           margin-bottom: 12px;
//         }
//         .new-chat-btn {
//           width: 100%;
//           margin-bottom: 20px;
//           background: transparent;
//           color: white;
//           border: 2px solid white;
//           padding: 10px;
//           border-radius: 8px;
//           cursor: pointer;
//           font-weight: bold;
//         }
//         .chat-link {
//           display: block;
//           width: 100%;
//           padding: 10px 12px;
//           margin-bottom: 8px;
//           background: white;
//           color: #1e3a8a;
//           border: none;
//           border-radius: 6px;
//           text-align: left;
//           cursor: pointer;
//         }
//         .chat-link:hover {
//           background: #e0e7ff;
//         }
//         .chat-link.active {
//           background-color: #c7d2fe;
//           font-weight: bold;
//         }
//         .chat-panel {
//           flex: 1;
//           background: #f3f4f6;
//           display: flex;
//           flex-direction: column;
//           position: relative;
//         }
//         .messages {
//           flex: 1;
//           padding: 20px;
//           overflow-y: auto;
//           display: flex;
//           flex-direction: column;
//           gap: 12px;
//           margin-bottom: 60px;
//         }
//         .message {
//           max-width: 65%;
//           padding: 12px 16px;
//           border-radius: 20px;
//           box-shadow: 0 2px 6px rgba(0,0,0,0.08);
//         }
//         .user {
//           align-self: flex-end;
//           background: #1d4ed8;
//           color: white;
//         }
//         .bot {
//           align-self: flex-start;
//           background: white;
//           color: #1f2937;
//         }
//         .input-bar {
//           position: absolute;
//           bottom: 0;
//           left: 0;
//           right: 0;
//           padding: 10px 20px;
//           display: flex;
//           gap: 10px;
//           background: #f3f4f6;
//         }
//         .input-box {
//           flex: 1;
//           padding: 14px;
//           border-radius: 30px;
//           border: 1px solid #ccc;
//         }
//         .send-btn {
//           padding: 14px 24px;
//           border-radius: 30px;
//           background: #1e3a8a;
//           color: white;
//           font-weight: bold;
//           border: none;
//           cursor: pointer;
//         }
//         .send-btn:disabled {
//           background: #9ca3af;
//           cursor: not-allowed;
//         }
//       `}</style>

//       <div className="sidebar">
//         <h3>Chats</h3>
//         <button className="new-chat-btn" onClick={handleNewChat}>
//           + New Chat
//         </button>
//         {conversations.map(chat => {
//           const firstMessage = chat.messages?.find(m => m.sender === 'user')?.content;
//           const label = firstMessage
//             ? firstMessage.slice(0, 25) + (firstMessage.length > 25 ? '...' : '')
//             : `Started on ${new Date(chat.started_at).toLocaleDateString()}`;

//           return (
//             <button
//               key={chat.id}
//               onClick={() => handleSelectChat(chat)}
//               className={`chat-link ${selectedChat?.id === chat.id ? 'active' : ''}`}
//             >
//               {label}
//             </button>
//           );
//         })}
//       </div>

//       <div className="chat-panel">
//         <div className="messages">
//           {messages.length === 0 && !loading && (
//             <div style={{ color: '#777', textAlign: 'center', marginTop: '50px' }}>
//               Start the conversation
//             </div>
//           )}
//           {messages.map((msg, i) => (
//                   <div key={i} className={`message ${msg.sender === 'user' ? 'user' : 'bot'}`}>
//           <div>{msg.content}</div>
//           {msg.sender === 'bot' && msg.emotion && (
//             <div style={{ fontSize: '12px', marginTop: '6px', color: '#6b7280' }}>
//               Emotion detected: <strong>{msg.emotion}</strong>
//             </div>
//           )}
//         </div>
//           ))}
//           {loading && (
//             <div className="message bot">
//               Mindora is typing...
//             </div>
//           )}
//           <div ref={messagesEndRef} />
//         </div>

//         {selectedChat && (
//           <div className="input-bar">
//             <input
//               className="input-box"
//               value={input}
//               onChange={e => setInput(e.target.value)}
//               placeholder="Type your message..."
//             />
//             <button
//               className="send-btn"
//               onClick={handleSend}
//               disabled={loading || !input.trim()}
//             >
//               Send
//             </button>
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }
import { useEffect, useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { sendMessage } from '../api/api';

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
    try {
      const res = await axios.get(`http://localhost:8000/auth/conversations/${conversationId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
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
      const newChat = { id: res.data.id, started_at: res.data.started_at };
      setSelectedChat(newChat);
    } catch (err) {
      handleError(err, 'Failed to create new chat');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedChat) return;

    const userMsg = {
      sender: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await sendMessage(selectedChat.id, input);

      if (!res || !res.response || !res.response.content) {
        throw new Error('Invalid bot response');
      }

      const botMsg = {
        sender: 'bot',
        content: res.response.content,
        timestamp: res.response.timestamp || new Date().toISOString(),
        emotion: res.emotion || null
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      handleError(err, 'Failed to send message');
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

      <div className="sidebar">
        <h3>Chats</h3>
        <button className="new-chat-btn" onClick={handleNewChat}>
          + New Chat
        </button>
        {conversations.map(chat => {
          const firstMessage = chat.messages?.find(m => m.sender === 'user')?.content;
          const label = firstMessage
            ? firstMessage.slice(0, 25) + (firstMessage.length > 25 ? '...' : '')
            : `Started on ${new Date(chat.started_at).toLocaleDateString()}`;

          return (
            <button
              key={chat.id}
              onClick={() => handleSelectChat(chat)}
              className={`chat-link ${selectedChat?.id === chat.id ? 'active' : ''}`}
            >
              {label}
            </button>
          );
        })}
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
                <div style={{ fontSize: '12px', marginTop: '6px', color: '#6b7280' }}>
                  Emotion detected: <strong>{msg.emotion}</strong>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="message bot">
              Mindora is typing...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

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
