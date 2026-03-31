import React, { useState } from "react";

const pages = ["🏠 Intro", "💬 Chat", "📊 Dashboard", "📁 History"];

const App = () => {
  const [page, setPage] = useState("🏠 Intro");
  const [messages, setMessages] = useState([]);
  const [images, setImages] = useState([]);
  const [voiceInputs, setVoiceInputs] = useState(0);
  const [userInput, setUserInput] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const resetSession = () => {
    setMessages([]);
    setImages([]);
    setVoiceInputs(0);
    setUserInput("");
    setStatusMessage("");
    setPage("🏠 Intro");
  };

  const appendMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };

  const sendText = async () => {
    if (!userInput.trim()) return;

    const question = {
      role: "user",
      type: "text",
      content: userInput.trim(),
    };

    appendMessage(question);
    setUserInput("");
    setStatusMessage("Sending question...");

    try {
      const response = await fetch("/api/send-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: question.content }),
      });
      const data = await response.json();
      appendMessage({
        role: "assistant",
        type: "text",
        content: data.response || data.message || "No response received.",
      });
      setStatusMessage("Response received.");
    } catch (error) {
      setStatusMessage("Unable to send question. Check backend.");
      appendMessage({
        role: "assistant",
        type: "text",
        content: "Error: unable to reach backend.",
      });
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const localUrl = URL.createObjectURL(file);
    const imageMessage = {
      role: "user",
      type: "image",
      name: file.name,
      path: localUrl,
      content: `Uploaded image: ${file.name}`,
    };

    appendMessage(imageMessage);
    setImages((prev) => [...prev, localUrl]);
    setStatusMessage("Uploading image...");

    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await fetch("/api/send-image", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      appendMessage({
        role: "assistant",
        type: "text",
        content: data.response || "Image analysis complete.",
      });
      setStatusMessage("Image analyzed.");
    } catch (error) {
      setStatusMessage("Image upload failed.");
      appendMessage({
        role: "assistant",
        type: "text",
        content: "Error: image backend not available.",
      });
    }
  };

  const handleAudioUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setVoiceInputs((prev) => prev + 1);
    setStatusMessage("Uploading voice note...");

    try {
      const formData = new FormData();
      formData.append("audio", file);
      const response = await fetch("/api/send-voice", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      appendMessage({
        role: "user",
        type: "text",
        content: `🎤 ${data.transcription || "Voice note received."}`,
      });
      appendMessage({
        role: "assistant",
        type: "text",
        content: data.response || "Voice analysis complete.",
      });
      setStatusMessage("Voice note analyzed.");
    } catch (error) {
      setStatusMessage("Voice upload failed.");
      appendMessage({
        role: "assistant",
        type: "text",
        content: "Error: voice backend not available.",
      });
    }
  };

  const renderSidebar = () => (
    <aside style={styles.sidebar}>
      <div>
        <h1>GramAI</h1>
        <p>Medical AI for triage, image review, and voice-assisted consultation.</p>
      </div>

      <div style={styles.navGroup}>
        {pages.map((item) => (
          <button
            key={item}
            onClick={() => setPage(item)}
            style={page === item ? styles.activeNavButton : styles.navButton}
          >
            {item}
          </button>
        ))}
      </div>

      <button style={styles.resetButton} onClick={resetSession}>
        🔁 Reset session
      </button>

      <div style={styles.helpBox}>
        <strong>How to use</strong>
        <ul>
          <li>Ask a clinical question.</li>
          <li>Upload images for analysis.</li>
          <li>Send voice notes for transcription.</li>
          <li>Review dashboard insights.</li>
        </ul>
      </div>
    </aside>
  );

  const renderIntro = () => (
    <section>
      <h2>Welcome to GramAI</h2>
      <p>
        GramAI combines text, image, and voice tools into one medical assistant interface.
      </p>
      <button style={styles.primaryButton} onClick={() => setPage("💬 Chat")}>🚀 Start Chat</button>

      <div style={styles.metricRow}>
        <div style={styles.metricCard}><strong>Queries</strong><span>{messages.filter((m) => m.role === "user").length}</span></div>
        <div style={styles.metricCard}><strong>Images</strong><span>{images.length}</span></div>
        <div style={styles.metricCard}><strong>Voice Notes</strong><span>{voiceInputs}</span></div>
      </div>

      <div style={styles.featureGrid}>
        <div style={styles.featureCard}>💬 Ask a medical question</div>
        <div style={styles.featureCard}>🖼️ Upload a scan or photo</div>
        <div style={styles.featureCard}>🎤 Send a voice note</div>
      </div>
    </section>
  );

  const renderChat = () => (
    <section>
      <h2>💬 Medical Chat</h2>
      <div style={styles.metricRow}>
        <div style={styles.metricCard}><strong>Total messages</strong><span>{messages.length}</span></div>
        <div style={styles.metricCard}><strong>Images</strong><span>{images.length}</span></div>
        <div style={styles.metricCard}><strong>Voice notes</strong><span>{voiceInputs}</span></div>
        <div style={styles.metricCard}><strong>Assistant replies</strong><span>{messages.filter((m) => m.role === "assistant").length}</span></div>
      </div>

      <div style={styles.chatWindow}>
        {messages.length === 0 && <div style={styles.emptyState}>Send a question or upload a file to begin the conversation.</div>}
        {messages.map((msg, index) => (
          <div key={index} style={msg.role === "user" ? styles.userBubble : styles.assistantBubble}>
            <div style={styles.messageRole}>{msg.role === "user" ? "You" : "Assistant"}</div>
            {msg.type === "image" ? (
              <div>
                <img src={msg.path} alt={msg.name} style={styles.uploadedImage} />
                <p>{msg.content}</p>
              </div>
            ) : (
              <p>{msg.content}</p>
            )}
          </div>
        ))}
      </div>

      <div style={styles.formRow}>
        <div style={{ flex: 3 }}>
          <input
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Ask your medical question here"
            style={styles.textInput}
          />
          <button style={styles.primaryButton} onClick={sendText}>Send</button>
        </div>

        <div style={styles.uploadColumn}>
          <label style={styles.uploadLabel}>
            Upload image
            <input type="file" accept="image/png, image/jpeg" onChange={handleImageUpload} style={styles.fileInput} />
          </label>
          <label style={styles.uploadLabel}>
            Upload voice note
            <input type="file" accept="audio/wav" onChange={handleAudioUpload} style={styles.fileInput} />
          </label>
        </div>
      </div>

      {statusMessage && <div style={styles.statusBar}>{statusMessage}</div>}
    </section>
  );

  const renderDashboard = () => (
    <section>
      <h2>📊 Dashboard</h2>
      <div style={styles.metricRow}>
        <div style={styles.metricCard}><strong>Total Queries</strong><span>{messages.filter((m) => m.role === "user").length}</span></div>
        <div style={styles.metricCard}><strong>Images uploaded</strong><span>{images.length}</span></div>
        <div style={styles.metricCard}><strong>Voice notes</strong><span>{voiceInputs}</span></div>
        <div style={styles.metricCard}><strong>Assistant replies</strong><span>{messages.filter((m) => m.role === "assistant").length}</span></div>
      </div>

      <div style={styles.recentList}>
        <h3>Recent activity</h3>
        {messages.slice(-5).map((msg, index) => (
          <div key={index} style={styles.recentItem}>
            <strong>{msg.role === "user" ? "User" : "Assistant"}</strong>: {msg.content || msg.name}
          </div>
        ))}
      </div>
    </section>
  );

  const renderHistory = () => (
    <section>
      <h2>📁 History</h2>
      {messages.length === 0 ? (
        <div style={styles.emptyState}>No history yet. Start a chat to save interactions.</div>
      ) : (
        messages.map((msg, index) => (
          <div key={index} style={styles.historyItem}>
            <strong>{index + 1}. {msg.role === "user" ? "User" : "Assistant"}</strong>
            <p>{msg.content || msg.name}</p>
          </div>
        ))
      )}
    </section>
  );

  return (
    <div style={styles.page}>
      {renderSidebar()}
      <main style={styles.content}>
        {page === "🏠 Intro" && renderIntro()}
        {page === "💬 Chat" && renderChat()}
        {page === "📊 Dashboard" && renderDashboard()}
        {page === "📁 History" && renderHistory()}
      </main>
    </div>
  );
};

const styles = {
  page: {
    display: "flex",
    minHeight: "100vh",
    fontFamily: "Arial, sans-serif",
    backgroundColor: "#f6f9fb",
    color: "#1f2937",
  },
  sidebar: {
    width: 300,
    padding: 24,
    background: "#0f172a",
    color: "#f8fafc",
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  navGroup: {
    display: "grid",
    gap: 8,
  },
  navButton: {
    padding: "12px 16px",
    border: "none",
    borderRadius: 8,
    background: "#1e293b",
    color: "#e2e8f0",
    cursor: "pointer",
    textAlign: "left",
  },
  activeNavButton: {
    padding: "12px 16px",
    border: "none",
    borderRadius: 8,
    background: "#3b82f6",
    color: "#ffffff",
    cursor: "pointer",
    textAlign: "left",
  },
  resetButton: {
    padding: "12px 16px",
    border: "none",
    borderRadius: 8,
    background: "#ef4444",
    color: "#ffffff",
    cursor: "pointer",
  },
  helpBox: {
    padding: 16,
    borderRadius: 12,
    background: "#111827",
    fontSize: 14,
    lineHeight: 1.6,
  },
  content: {
    flex: 1,
    padding: 32,
  },
  primaryButton: {
    padding: "12px 20px",
    borderRadius: 10,
    border: "none",
    background: "#3b82f6",
    color: "white",
    cursor: "pointer",
    fontSize: 16,
    marginTop: 16,
  },
  metricRow: {
    display: "grid",
    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    gap: 16,
    marginTop: 24,
  },
  metricCard: {
    background: "#ffffff",
    borderRadius: 16,
    padding: 20,
    boxShadow: "0 8px 20px rgba(15, 23, 42, 0.08)",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  featureGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    gap: 16,
    marginTop: 24,
  },
  featureCard: {
    background: "#ffffff",
    borderRadius: 16,
    padding: 20,
    boxShadow: "0 6px 18px rgba(15, 23, 42, 0.08)",
  },
  chatWindow: {
    background: "#ffffff",
    borderRadius: 20,
    padding: 24,
    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
    display: "flex",
    flexDirection: "column",
    gap: 16,
    marginTop: 24,
  },
  userBubble: {
    alignSelf: "flex-end",
    maxWidth: "80%",
    background: "#e0f2fe",
    borderRadius: 16,
    padding: 16,
  },
  assistantBubble: {
    alignSelf: "flex-start",
    maxWidth: "80%",
    background: "#f8fafc",
    borderRadius: 16,
    padding: 16,
  },
  messageRole: {
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 8,
  },
  formRow: {
    display: "grid",
    gridTemplateColumns: "3fr 1fr",
    gap: 20,
    marginTop: 28,
  },
  textInput: {
    width: "100%",
    padding: "14px 16px",
    borderRadius: 12,
    border: "1px solid #cbd5e1",
    fontSize: 16,
  },
  uploadColumn: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  uploadLabel: {
    display: "flex",
    flexDirection: "column",
    padding: 16,
    background: "#ffffff",
    borderRadius: 16,
    border: "1px dashed #cbd5e1",
    cursor: "pointer",
  },
  fileInput: {
    marginTop: 12,
  },
  uploadedImage: {
    width: "100%",
    borderRadius: 12,
    marginTop: 12,
  },
  statusBar: {
    marginTop: 20,
    padding: 14,
    borderRadius: 12,
    background: "#e2e8f0",
  },
  recentList: {
    marginTop: 24,
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  recentItem: {
    background: "#ffffff",
    borderRadius: 12,
    padding: 16,
    boxShadow: "0 6px 18px rgba(15, 23, 42, 0.06)",
  },
  historyItem: {
    background: "#ffffff",
    borderRadius: 12,
    padding: 16,
    boxShadow: "0 6px 18px rgba(15, 23, 42, 0.06)",
    marginBottom: 16,
  },
  emptyState: {
    borderRadius: 16,
    background: "#f8fafc",
    padding: 24,
    textAlign: "center",
  },
};

export default App;
