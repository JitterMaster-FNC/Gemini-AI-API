import { useState, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null); 
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const imageInputRef = useRef(null);
  const fileInputRef = useRef(null);

  const segoeFont = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
  const activeChat = chats.find(c => c.id === activeChatId);

  const goToLanding = () => {
    setActiveChatId(null); 
    setMenuOpenId(null);
    setAttachmentMenuOpen(false);
    setSelectedFile(null);
  };

  const deleteChat = (e, id) => {
    e.stopPropagation();
    const updatedChats = chats.filter(c => c.id !== id);
    setChats(updatedChats);
    if (id === activeChatId) setActiveChatId(null);
    setMenuOpenId(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
    setAttachmentMenuOpen(false);
  };

  const sendMessage = async () => {
    if ((!input && !selectedFile) || loading) return;

    const userMessage = { 
      role: 'user', 
      text: input, 
      fileName: selectedFile ? selectedFile.name : null 
    };
    const currentInput = input;
    const currentFile = selectedFile;

    setInput('');
    setSelectedFile(null);
    setLoading(true);

    let currentChatId = activeChatId;

    if (currentChatId === null) {
      const newId = Date.now();
      const newChat = {
        id: newId,
        title: '...', 
        messages: [userMessage]
      };
      setChats([newChat, ...chats]);
      setActiveChatId(newId);
      currentChatId = newId;

      axios.post('http://localhost:8000/generate_title', { message: currentInput || "ファイル添付" })
        .then(res => {
          setChats(prev => prev.map(c => c.id === newId ? { ...c, title: res.data.title } : c));
        })
        .catch(() => {
          setChats(prev => prev.map(c => c.id === newId ? { ...c, title: '新しいチャット' } : c));
        });
    } else {
      setChats(prev => prev.map(chat => {
        if (chat.id === currentChatId) {
          return { ...chat, messages: [...chat.messages, userMessage] };
        }
        return chat;
      }));
    }

    try {
      const formData = new FormData();
      formData.append('message', currentInput);
      if (currentFile) {
        formData.append('file', currentFile);
      }

      const res = await axios.post('http://localhost:8000/chat', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const aiMessage = { role: 'ai', text: res.data.reply || res.data.error };
      
      setChats(prev => prev.map(chat => {
        if (chat.id === currentChatId) {
          return { ...chat, messages: [...chat.messages, aiMessage] };
        }
        return chat;
      }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderInputSection = (isLanding) => (
    <div style={isLanding ? { width: '100%', maxWidth: '750px', marginTop: '30px' } : { 
      position: 'absolute', bottom: '40px', left: '50%', transform: 'translateX(-50%)', width: '90%', maxWidth: '750px' 
    }}>
      {selectedFile && (
        <div style={{ backgroundColor: '#333', padding: '5px 15px', borderRadius: '10px 10px 0 0', fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between', border: '1px solid #444', borderBottom: 'none', width: 'fit-content', marginLeft: '20px' }}>
          📎 {selectedFile.name}
          <span onClick={() => setSelectedFile(null)} style={{ marginLeft: '10px', cursor: 'pointer', color: '#ff4b4b' }}>×</span>
        </div>
      )}
      <div style={{ backgroundColor: '#2d2d2d', borderRadius: selectedFile ? '0 15px 15px 15px' : '15px', padding: '15px 20px', display: 'flex', alignItems: 'center', boxShadow: '0 0 20px rgba(0,0,0,0.4)', border: '1px solid #444', position: 'relative' }}>
        
        <div style={{ position: 'relative' }}>
          <span 
            onClick={() => setAttachmentMenuOpen(!attachmentMenuOpen)}
            style={{ color: '#888', marginRight: '15px', fontSize: '1.5rem', lineHeight: '0', cursor: 'pointer', userSelect: 'none' }}
          >
            +
          </span>
          {attachmentMenuOpen && (
            <div style={{ position: 'absolute', bottom: '40px', left: '0', backgroundColor: '#171717', border: '1px solid #444', borderRadius: '8px', zIndex: 200, width: '150px', boxShadow: '0 5px 15px rgba(0,0,0,0.5)' }}>
              <div 
                onClick={() => imageInputRef.current.click()}
                style={{ padding: '12px', fontSize: '0.9rem', cursor: 'pointer', borderBottom: '1px solid #333' }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#2b2b2b'}
                onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                画像を添付
              </div>
              <div 
                onClick={() => fileInputRef.current.click()}
                style={{ padding: '12px', fontSize: '0.9rem', cursor: 'pointer' }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#2b2b2b'}
                onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                ファイルを添付
              </div>
            </div>
          )}
        </div>

        <input 
          type="file" 
          ref={imageInputRef} 
          style={{ display: 'none' }} 
          accept="image/*" 
          onChange={handleFileChange} 
        />
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileChange} 
        />

        <input 
          style={{ flex: 1, backgroundColor: 'transparent', border: 'none', color: 'white', fontSize: '1.1rem', outline: 'none', fontFamily: segoeFont }}
          placeholder="メッセージを送信"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
      </div>
      <p style={{ fontSize: '0.7rem', color: '#8e8ea0', textAlign: 'center', marginTop: '10px' }}>
        AIの回答は必ずしも正しいとは限りません。重要な情報は確認するようにしてください。
      </p>
    </div>
  );

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', backgroundColor: '#1e1e1e', color: 'white', fontFamily: segoeFont, overflow: 'hidden' }}>
      
      <div style={{ width: '260px', backgroundColor: '#171717', display: 'flex', flexDirection: 'column', padding: '10px', boxSizing: 'border-box', borderRight: '1px solid #333' }}>
        <button 
          onClick={goToLanding}
          style={{ 
            padding: '12px', marginBottom: '20px', cursor: 'pointer', backgroundColor: 'transparent', color: 'white', border: '1px solid #444', borderRadius: '5px', textAlign: 'left', fontSize: '0.9rem', fontFamily: segoeFont, display: 'flex', alignItems: 'center' 
          }}
        >
          <span style={{ marginRight: '10px', fontSize: '1.2rem', fontWeight: 'bold' }}>+</span>
          新しいチャットを作成
        </button>

        <div style={{ overflowY: 'auto', flex: 1 }}>
          <p style={{ fontSize: '0.75rem', color: '#8e8ea0', fontWeight: 'bold', margin: '10px 5px' }}>会話履歴</p>
          {chats.map(chat => (
            <div 
              key={chat.id}
              onClick={() => setActiveChatId(chat.id)}
              style={{ position: 'relative', padding: '12px', margin: '2px 0', cursor: 'pointer', borderRadius: '5px', backgroundColor: chat.id === activeChatId ? '#2b2b2b' : 'transparent', fontSize: '0.9rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', width: '80%' }}>
                {chat.title}
              </span>
              <div onClick={(e) => { e.stopPropagation(); setMenuOpenId(menuOpenId === chat.id ? null : chat.id); }} style={{ padding: '0 5px', fontSize: '1.2rem', color: '#8e8ea0' }}>⋮</div>
              {menuOpenId === chat.id && (
                <div style={{ position: 'absolute', right: '10px', top: '40px', backgroundColor: '#050505', border: '1px solid #444', borderRadius: '5px', zIndex: 100 }}>
                  <div onClick={(e) => deleteChat(e, chat.id)} style={{ padding: '10px 20px', color: '#ff4b4b', cursor: 'pointer', fontSize: '0.85rem' }}>削除</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', overflowY: 'auto', padding: !activeChat ? '0' : '40px 20px 150px 20px', justifyContent: !activeChat ? 'center' : 'flex-start' }}>
          {!activeChat ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
               <h1 style={{ fontSize: '4rem', fontWeight: 'bold', letterSpacing: '-1px', margin: '0' }}>MY AI API</h1>
               {renderInputSection(true)}
            </div>
          ) : (
            <div style={{ width: '100%', maxWidth: '800px' }}>
              {activeChat.messages.map((msg, i) => (
                <div key={i} style={{ marginBottom: '30px', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                  <div className="markdown-body" style={{
                    display: 'inline-block', padding: '15px 25px', borderRadius: '20px', backgroundColor: msg.role === 'user' ? '#333' : '#262626', border: msg.role === 'user' ? 'none' : '1px solid #444', lineHeight: '1.6', maxWidth: '85%', textAlign: 'left', color: '#ececf1', wordBreak: 'break-word'
                  }}>
                    {msg.fileName && <div style={{ fontSize: '0.8rem', color: '#aaa', marginBottom: '5px', borderBottom: '1px solid #444', paddingBottom: '5px' }}>📎 {msg.fileName}</div>}
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  </div>
                </div>
              ))}
              {loading && <p style={{ color: '#888', textAlign: 'center' }}>回答中...</p>}
            </div>
          )}
        </div>
        {activeChat && renderInputSection(false)}
      </div>
      <style>{`
        .markdown-body table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        .markdown-body th, .markdown-body td { border: 1px solid #444; padding: 8px; text-align: left; }
        .markdown-body th { backgroundColor: #333; }
        .markdown-body p { margin: 8px 0; }
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { margin: 16px 0 8px 0; }
      `}</style>
    </div>
  )
}

export default App