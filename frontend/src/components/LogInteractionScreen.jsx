import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchHCPs, setSelectedHcp, sendMessage } from '../store/crmSlice';
import { Send, User, Calendar, MessageSquare, ShieldCheck, FileText, Clock, Users, BookOpen, Package, CheckCircle, ArrowRight, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LogInteractionScreen = () => {
  const dispatch = useDispatch();
  const { hcps, selectedHcp, chatHistory, loading } = useSelector((state) => state.crm);
  const [chatInput, setChatInput] = useState('');
  const [formData, setFormData] = useState({
    type: 'Meeting',
    date: new Date().toISOString().split('T')[0],
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
    attendees: '',
    topics_discussed: '',
    materials_shared: [],
    samples_distributed: [],
    sentiment: 'Neutral',
    outcomes: '',
    next_steps: ''
  });

  const formatTimeTo24h = (timeStr) => {
    if (!timeStr) return '';

    // Clean the string
    const cleanTime = timeStr.trim().toUpperCase();

    // Check if already HH:mm
    if (/^([01]\d|2[0-3]):([0-5]\d)$/.test(cleanTime)) {
      return cleanTime;
    }

    // Handle formats like "2 PM", "2:30 PM", "2PM", "14:00"
    try {
      const match = cleanTime.match(/(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?/);
      if (!match) return timeStr;

      let [_, hours, minutes, modifier] = match;
      hours = parseInt(hours, 10);
      minutes = minutes ? parseInt(minutes, 10) : 0;

      if (modifier === 'PM' && hours < 12) hours += 12;
      if (modifier === 'AM' && hours === 12) hours = 0;

      return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    } catch (e) {
      console.warn("Failed to parse time:", timeStr);
      return timeStr;
    }
  };

  const formatDateYYYYMMDD = (dateStr) => {
    if (!dateStr) return '';
    
    const cleanDate = dateStr.trim().toLowerCase();
    
    // Handle relative dates
    if (cleanDate === 'today') {
      return new Date().toISOString().split('T')[0];
    }
    if (cleanDate === 'yesterday') {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      return d.toISOString().split('T')[0];
    }

    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toISOString().split('T')[0];
    } catch (e) {
      return dateStr;
    }
  };

  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  // Listen for AI messages that contain structured data
  useEffect(() => {
    const lastMsg = chatHistory[chatHistory.length - 1];
    if (lastMsg && lastMsg.role === 'ai' && lastMsg.content.includes('UI_UPDATE_DATA:')) {
      try {
        let jsonStr = lastMsg.content.split('UI_UPDATE_DATA:')[1].trim();

        // Robust JSON cleaning
        jsonStr = jsonStr.replace(/```json/g, '').replace(/```/g, '').trim();

        // Attempt to fix common JSON errors (like single quotes or unquoted keys)
        // Note: This is a best-effort approach
        let sanitizedJson = jsonStr;
        if (!jsonStr.startsWith('{')) {
          const match = jsonStr.match(/\{[\s\S]*\}/);
          if (match) sanitizedJson = match[0];
        }

        const extractedData = JSON.parse(sanitizedJson);

        setFormData(prev => ({
          ...prev,
          ...Object.keys(extractedData).reduce((acc, key) => {
            const val = extractedData[key];
            if (val !== null && val !== 'null' && val !== undefined && val !== '') {
              let parsedValue = val;
              if (key === 'time') parsedValue = formatTimeTo24h(parsedValue);
              if (key === 'date') parsedValue = formatDateYYYYMMDD(parsedValue);
              
              // Only overwrite if it actually holds data.
              if (parsedValue !== null && parsedValue !== 'null' && parsedValue !== '') {
                  acc[key] = parsedValue;
              }
            }
            return acc;
          }, {})
        }));
      } catch (err) {
        console.error("Failed to parse AI update data:", err);
      }
    }
  }, [chatHistory]);

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;
    dispatch(sendMessage({ message: chatInput, hcpId: selectedHcp?.id }));
    setChatInput('');
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    alert('Interaction Saved Successfully!');
  };

  return (
    <div className="container" style={{ maxWidth: '1400px' }}>
      <header style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Log HCP Interaction</h1>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.5fr) minmax(0, 1fr)', gap: '24px', alignItems: 'start' }}>
        {/* Left: Structured Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card"
          style={{ padding: '24px', border: '1px solid rgba(255,255,255,0.1)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <FileText size={20} className="text-primary" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Interaction Details</h2>
          </div>

          <form onSubmit={handleFormSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* HCP & Type */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <label className="label">HCP Name</label>
                <select
                  className="input-field"
                  value={selectedHcp?.id || ''}
                  onChange={(e) => dispatch(setSelectedHcp(hcps.find(h => h.id === parseInt(e.target.value))))}
                >
                  {hcps.map(hcp => (
                    <option key={hcp.id} value={hcp.id}>{hcp.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Interaction Type</label>
                <select className="input-field" value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })}>
                  <option>Meeting</option>
                  <option>Call</option>
                  <option>Email</option>
                </select>
              </div>
            </div>

            {/* Date & Time */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <label className="label">Date</label>
                <div style={{ position: 'relative' }}>
                  <input type="date" className="input-field" value={formData.date} onChange={(e) => setFormData({ ...formData, date: e.target.value })} />
                  <Calendar size={16} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5, pointerEvents: 'none' }} />
                </div>
              </div>
              <div>
                <label className="label">Time</label>
                <div style={{ position: 'relative' }}>
                  <input type="time" className="input-field" value={formData.time} onChange={(e) => setFormData({ ...formData, time: e.target.value })} />
                  <Clock size={16} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5, pointerEvents: 'none' }} />
                </div>
              </div>
            </div>

            {/* Attendees */}
            <div>
              <label className="label">Attendees</label>
              <div style={{ position: 'relative' }}>
                <input
                  className="input-field"
                  placeholder="Enter names or search..."
                  value={formData.attendees}
                  onChange={(e) => setFormData({ ...formData, attendees: e.target.value })}
                />
                <Users size={16} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} />
              </div>
            </div>

            {/* Topics Discussed */}
            <div>
              <label className="label">Topics Discussed</label>
              <textarea
                className="input-field"
                rows="4"
                placeholder="Enter key discussion points..."
                value={formData.topics_discussed}
                onChange={(e) => setFormData({ ...formData, topics_discussed: e.target.value })}
              ></textarea>
            </div>

            {/* Materials & Samples */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="nested-card" style={{ padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <label className="label" style={{ marginBottom: 0 }}>Materials Shared</label>
                  <button type="button" style={{ fontSize: '0.75rem', color: 'var(--primary)', background: 'none', border: 'none', cursor: 'pointer' }}>Search/Add</button>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {formData.materials_shared.length > 0 ? formData.materials_shared.join(', ') : 'No materials added.'}
                </div>
              </div>
              <div className="nested-card" style={{ padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <label className="label" style={{ marginBottom: 0 }}>Samples Distributed</label>
                  <button type="button" style={{ fontSize: '0.75rem', color: 'var(--primary)', background: 'none', border: 'none', cursor: 'pointer' }}>Add Sample</button>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {formData.samples_distributed.length > 0 ? formData.samples_distributed.join(', ') : 'No samples added.'}
                </div>
              </div>
            </div>

            {/* Sentiment */}
            <div>
              <label className="label">Observed HCP Sentiment</label>
              <div style={{ display: 'flex', gap: '24px' }}>
                {['Positive', 'Neutral', 'Negative'].map(s => (
                  <label key={s} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem' }}>
                    <input
                      type="radio"
                      name="sentiment"
                      checked={formData.sentiment === s}
                      onChange={() => setFormData({ ...formData, sentiment: s })}
                      style={{ accentColor: 'var(--primary)' }}
                    />
                    {s === 'Positive' ? '😊 Positive' : s === 'Neutral' ? '😐 Neutral' : '☹️ Negative'}
                  </label>
                ))}
              </div>
            </div>

            {/* Outcomes */}
            <div>
              <label className="label">Outcomes</label>
              <textarea
                className="input-field"
                rows="3"
                placeholder="Key outcomes or agreements..."
                value={formData.outcomes}
                onChange={(e) => setFormData({ ...formData, outcomes: e.target.value })}
              ></textarea>
            </div>

            {/* Follow-up Actions */}
            <div>
              <label className="label">Follow-up Actions</label>
              <textarea
                className="input-field"
                rows="3"
                placeholder="Enter next steps or tasks..."
                value={formData.next_steps}
                onChange={(e) => setFormData({ ...formData, next_steps: e.target.value })}
              ></textarea>
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', padding: '16px', fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              <ArrowRight size={18} /> Save Interaction
            </button>
          </form>
        </motion.div>

        {/* Right: AI Assistant */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card"
            style={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid rgba(16, 185, 129, 0.2)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Zap size={18} color="#10b981" />
              </div>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '2px' }}>AI Assistant</h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Log interaction via chat</p>
              </div>
            </div>

            <div style={{
              flex: 1,
              background: 'rgba(0,0,0,0.15)',
              borderRadius: '16px',
              padding: '20px',
              marginBottom: '20px',
              overflowY: 'auto',
              minHeight: '400px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <AnimatePresence>
                {chatHistory.length === 0 ? (
                  <div key="empty" style={{ margin: 'auto', textAlign: 'center', maxWidth: '200px' }}>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.
                    </p>
                  </div>
                ) : (
                  chatHistory.map((msg, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}
                    >
                      <div style={{
                        padding: '12px 16px',
                        borderRadius: '14px',
                        fontSize: '0.9rem',
                        lineHeight: 1.5,
                        background: msg.role === 'user' ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                        border: msg.role === 'user' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                      }}>
                        {msg.content.includes('UI_UPDATE_DATA:') ? msg.content.split('UI_UPDATE_DATA:')[0] : msg.content}
                      </div>
                    </motion.div>
                  ))
                )}
                {loading && (
                  <div style={{ alignSelf: 'flex-start' }}>
                    <div className="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                )}
              </AnimatePresence>
            </div>

            <div style={{ display: 'flex', gap: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '8px' }}>
              <input
                style={{ background: 'none', border: 'none', borderBottom: 'none', padding: '8px 12px', color: 'white', flex: 1, outline: 'none' }}
                placeholder="Describe interaction..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              />
              <button
                onClick={handleSendMessage}
                style={{ padding: '8px 16px', borderRadius: '8px', background: 'var(--primary)', border: 'none', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Send size={16} /> Log
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      <style>{`
        .label { display: block; margin-bottom: 8px; font-size: 0.8rem; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
        .text-primary { color: var(--primary); }
        .typing-indicator { display: flex; gap: 4px; padding: 12px 16px; background: rgba(255,255,255,0.05); border-radius: 14px; }
        .typing-indicator span { width: 6px; height: 6px; background: var(--text-muted); border-radius: 50%; opacity: 0.4; animation: blink 1.4s infinite; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
      `}</style>
    </div>
  );
};

export default LogInteractionScreen;
