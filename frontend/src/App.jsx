import { useState, useRef, useEffect } from "react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const EXAMPLE_TASKS = [
  "Reset password for john@company.com to NewPass@99",
  "Create a new user: Alice Brown, alice@company.com, Engineer, Engineering",
  "Assign GitHub license to sarah@company.com",
  "Check if mike@company.com exists, if not create them, then assign Figma license",
  "Deactivate mike@company.com",
  "List all users",
];

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: "1rem",
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: "50%", background: "#3b82f6",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 16, marginRight: 10, flexShrink: 0, marginTop: 2,
        }}>⚙️</div>
      )}
      <div style={{
        maxWidth: "75%",
        padding: "0.75rem 1rem",
        borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        background: isUser ? "#3b82f6" : "#1e293b",
        border: isUser ? "none" : "1px solid #334155",
        color: "#f1f5f9",
        fontSize: "0.9rem",
        lineHeight: 1.6,
        whiteSpace: "pre-wrap",
      }}>
        {msg.loading ? (
          <span style={{ color: "#64748b" }}>
            <LoadingDots /> Running agent…
          </span>
        ) : msg.content}
        {msg.steps > 0 && (
          <div style={{ marginTop: 6, fontSize: "0.75rem", color: "#64748b" }}>
            ✓ {msg.steps} browser steps
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingDots() {
  return (
    <span style={{ display: "inline-block", marginRight: 6 }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          display: "inline-block", width: 6, height: 6, borderRadius: "50%",
          background: "#60a5fa", marginRight: 3,
          animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </span>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "agent",
      content: "Hi! I'm your IT Support Agent. I can reset passwords, create users, manage licenses, and more.\n\nTry one of the examples below or type your own task.",
      steps: 0,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendTask(task) {
    if (!task.trim() || loading) return;
    setInput("");
    setLoading(true);

    const userMsg = { role: "user", content: task };
    const loadingMsg = { role: "agent", content: "", loading: true, steps: 0 };
    setMessages(prev => [...prev, userMsg, loadingMsg]);

    try {
      const res = await fetch(`${API_BASE}/api/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task }),
      });
      const data = await res.json();

      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "agent",
          content: data.success
            ? `✅ ${data.result}`
            : `❌ ${data.result}`,
          steps: data.steps || 0,
          loading: false,
        };
        return updated;
      });
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "agent",
          content: `❌ Could not connect to the agent. Make sure the backend is running at ${API_BASE}`,
          steps: 0,
          loading: false,
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendTask(input);
    }
  }

  return (
    <div style={{
      minHeight: "100vh", background: "#0f172a", display: "flex",
      flexDirection: "column", fontFamily: "'Segoe UI', system-ui, sans-serif",
    }}>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
      `}</style>

      {/* Header */}
      <header style={{
        background: "#1e293b", borderBottom: "1px solid #334155",
        padding: "1rem 1.5rem", display: "flex", alignItems: "center",
        justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10, background: "#3b82f6",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
          }}>⚙️</div>
          <div>
            <div style={{ fontWeight: 700, color: "#f1f5f9", fontSize: "1rem" }}>IT Support Agent</div>
            <div style={{ fontSize: "0.75rem", color: "#10b981" }}>● Powered by Gemini + browser-use</div>
          </div>
        </div>
        <a href={`${API_BASE}`} target="_blank" rel="noreferrer" style={{
          color: "#60a5fa", fontSize: "0.8rem", textDecoration: "none",
          border: "1px solid #334155", padding: "0.35rem 0.75rem", borderRadius: 8,
        }}>
          Open Admin Panel ↗
        </a>
      </header>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem" }}>
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        <div ref={bottomRef} />
      </div>

      {/* Example tasks */}
      <div style={{
        padding: "0 1.5rem 0.75rem", display: "flex", gap: 8, flexWrap: "wrap",
      }}>
        {EXAMPLE_TASKS.map((t, i) => (
          <button key={i} onClick={() => sendTask(t)} disabled={loading}
            style={{
              background: "transparent", border: "1px solid #334155",
              color: "#94a3b8", padding: "0.3rem 0.7rem", borderRadius: 20,
              fontSize: "0.75rem", cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.15s", whiteSpace: "nowrap",
            }}
            onMouseOver={e => { e.target.style.background = "#1e293b"; e.target.style.color = "#f1f5f9"; }}
            onMouseOut={e => { e.target.style.background = "transparent"; e.target.style.color = "#94a3b8"; }}
          >{t}</button>
        ))}
      </div>

      {/* Input */}
      <div style={{
        padding: "0.75rem 1.5rem 1.5rem",
        borderTop: "1px solid #1e293b",
      }}>
        <div style={{
          display: "flex", gap: 10, background: "#1e293b",
          border: "1px solid #334155", borderRadius: 14, padding: "0.5rem 0.5rem 0.5rem 1rem",
          alignItems: "flex-end",
        }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type an IT task… e.g. 'reset password for john@company.com'"
            disabled={loading}
            rows={1}
            style={{
              flex: 1, background: "transparent", border: "none", outline: "none",
              color: "#f1f5f9", fontSize: "0.9rem", resize: "none",
              lineHeight: 1.5, maxHeight: 120, overflowY: "auto",
              fontFamily: "inherit", padding: "0.25rem 0",
            }}
          />
          <button
            onClick={() => sendTask(input)}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim() ? "#334155" : "#3b82f6",
              color: "white", border: "none", borderRadius: 10,
              width: 38, height: 38, display: "flex", alignItems: "center",
              justifyContent: "center", cursor: loading ? "not-allowed" : "pointer",
              fontSize: 18, flexShrink: 0, transition: "background 0.15s",
            }}
          >{loading ? "⏳" : "↑"}</button>
        </div>
        <div style={{ textAlign: "center", marginTop: 8, fontSize: "0.7rem", color: "#475569" }}>
          Enter to send · The agent controls a real browser to complete tasks
        </div>
      </div>
    </div>
  );
}
