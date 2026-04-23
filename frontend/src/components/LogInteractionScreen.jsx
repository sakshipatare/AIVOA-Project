import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchHCPs, setSelectedHcp, sendMessage } from '../store/crmSlice';
import { Send, User, Calendar, MessageSquare, ShieldCheck, FileText, BarChart3 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LogInteractionScreen = () => {
  const dispatch = useDispatch();
  const { hcps, selectedHcp, chatHistory, loading } = useSelector((state) => state.crm);
  const [chatInput, setChatInput] = useState('');
  const [formData, setFormData] = useState({
    type: 'Meeting',
    summary: '',
    sentiment: 'Neutral'
  });

  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;
    dispatch(sendMessage({ message: chatInput, hcpId: selectedHcp?.id }));
    setChatInput('');
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    alert('Form implementation would save to DB. Use the AI Assistant for natural language logging!');
  };

  return (
    <div className="container">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="header"
        style={{ marginBottom: '40px' }}
      >
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Log HCP Interaction</h1>
        <p style={{ color: 'var(--text-muted)' }}>Capture clinical insights and manage HCP relationships with AI.</p>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
        {/* Left: Structured Form */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card" 
          style={{ padding: '32px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
            <FileText size={24} color="var(--primary)" />
            <h2 style={{ fontSize: '1.25rem' }}>Interaction Details</h2>
          </div>

          <form onSubmit={handleFormSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem', fontWeight: 500 }}>Select HCP</label>
              <select 
                className="input-field"
                value={selectedHcp?.id || ''}
                onChange={(e) => dispatch(setSelectedHcp(hcps.find(h => h.id === parseInt(e.target.value))))}
              >
                {hcps.map(hcp => (
                  <option key={hcp.id} value={hcp.id}>{hcp.name} ({hcp.specialty})</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem' }}>Type</label>
                <select className="input-field" value={formData.type} onChange={(e) => setFormData({...formData, type: e.target.value})}>
                  <option>Meeting</option>
                  <option>Call</option>
                  <option>Email</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem' }}>Sentiment</label>
                <select className="input-field" value={formData.sentiment} onChange={(e) => setFormData({...formData, sentiment: e.target.value})}>
                  <option>Positive</option>
                  <option>Neutral</option>
                  <option>Negative</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem' }}>Discussion Summary</label>
              <textarea 
                className="input-field" 
                rows="5" 
                style={{ resize: 'none' }}
                placeholder="Enter key discussion points..."
                value={formData.summary}
                onChange={(e) => setFormData({...formData, summary: e.target.value})}
              ></textarea>
            </div>

            <button type="submit" className="btn-primary" style={{ marginTop: '12px' }}>
              Save Interaction
            </button>
          </form>
        </motion.div>

        {/* Right: AI Assistant */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card" 
          style={{ padding: '32px', display: 'flex', flexDirection: 'column', height: '100%' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
            <ShieldCheck size={24} color="#10b981" />
            <h2 style={{ fontSize: '1.25rem' }}>AI Contextual Assistant</h2>
          </div>

          <div style={{ 
            flex: 1, 
            background: 'rgba(0,0,0,0.2)', 
            borderRadius: '12px', 
            padding: '16px', 
            marginBottom: '20px',
            overflowY: 'auto',
            minHeight: '300px'
          }}>
            <AnimatePresence>
              {chatHistory.length === 0 ? (
                <div key="empty-state" style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '100px' }}>
                  <MessageSquare size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
                  <p>How can I help you today?<br/>Try "Log a meeting with {selectedHcp?.name}"</p>
                </div>
              ) : (
                chatHistory.map((msg, i) => (
                  <motion.div 
                    key={`${msg.role}-${i}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ 
                      marginBottom: '16px', 
                      textAlign: msg.role === 'user' ? 'right' : 'left' 
                    }}
                  >
                    <div style={{ 
                      display: 'inline-block', 
                      padding: '12px 16px', 
                      borderRadius: '12px',
                      maxWidth: '80%',
                      background: msg.role === 'user' ? 'var(--primary)' : 'var(--glass)',
                      fontSize: '0.9rem'
                    }}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))
              )}
              {loading && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>AI is thinking...</div>}
            </AnimatePresence>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <input 
              className="input-field" 
              placeholder="Describe the interaction or ask a question..." 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <button className="btn-primary" style={{ padding: '12px' }} onClick={handleSendMessage}>
              <Send size={20} />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default LogInteractionScreen;
