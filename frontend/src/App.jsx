import { useState, useEffect, useCallback, useRef } from "react"
import axios from "axios"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import "./App.css"

const API = import.meta.env.VITE_API_URL || "/api"

function newSessionId() {
  return Math.random().toString(36).substring(2, 10)
}
function loadSessions() {
  try { const s = localStorage.getItem("rag_sessions"); return s ? JSON.parse(s) : null } catch { return null }
}
function saveSessions(sessions) {
  try { localStorage.setItem("rag_sessions", JSON.stringify(sessions)) } catch {}
}

export default function App() {
  const [sessions, setSessions] = useState(() => {
    const saved = loadSessions()
    if (saved && saved.length > 0) return saved
    return [{ id: newSessionId(), title: "New Chat", messages: [], uploadedFile: null, documents: [] }]
  })
  const [currentId, setCurrentId] = useState(() => {
    const saved = loadSessions()
    if (saved && saved.length > 0) {
      const lastId = localStorage.getItem("rag_active_session")
      if (lastId && saved.find((s) => s.id === lastId)) return lastId
      return saved[0].id
    }
    return null
  })

  const current = sessions.find((s) => s.id === currentId) || sessions[sessions.length - 1]

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [retrievalStatus, setRetrievalStatus] = useState("")
  const [streamingContent, setStreamingContent] = useState("")
  const [streamingCitations, setStreamingCitations] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState("")
  const [model, setModel] = useState("llama-3.1-8b-instant")
  const [models, setModels] = useState({})
  const [webSearch, setWebSearch] = useState(false)
  const [searchAllDocs, setSearchAllDocs] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [expandedCitation, setExpandedCitation] = useState(null)

  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const contentRef = useRef(null)
  const shouldAutoScroll = useRef(true)

  const handleScroll = useCallback(() => {
    if (!contentRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = contentRef.current
    shouldAutoScroll.current = scrollHeight - scrollTop - clientHeight < 100
  }, [])

  useEffect(() => {
    axios.get(`${API}/models`).then((r) => { if (r.data?.models) setModels(r.data.models) }).catch(() => {})
  }, [])

  useEffect(() => {
    const nonEmpty = sessions.filter((s) => s.messages.length > 0 || s.id === currentId)
    saveSessions(nonEmpty)
    if (currentId) localStorage.setItem("rag_active_session", currentId)
  }, [sessions, currentId])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }) }, [current.messages])
  useEffect(() => {
    if (streamingContent && shouldAutoScroll.current)
      messagesEndRef.current?.scrollIntoView({ behavior: "instant" })
  }, [streamingContent])

  const updateSession = useCallback((id, patch) => {
    setSessions((prev) => prev.map((s) => {
      if (s.id !== id) return s
      const p = typeof patch === "function" ? patch(s) : patch
      return { ...s, ...p }
    }))
  }, [])

  const newChat = useCallback(() => {
    const id = newSessionId()
    setSessions((prev) => [...prev, { id, title: "New Chat", messages: [], uploadedFile: null, documents: [] }])
    setCurrentId(id)
    setLoading(false)
    setStreamingContent("")
    setRetrievalStatus("")
  }, [])

  const switchSession = useCallback((id) => {
    setSessions((prev) => prev.filter((s) => s.id === id || s.messages.length > 0))
    setCurrentId(id)
    setLoading(false)
    setStreamingContent("")
    setRetrievalStatus("")
  }, [])

  const streamQuestion = useCallback(async (text, sessionId, skipUserMsg) => {
    if (!skipUserMsg) {
      updateSession(sessionId, (prev) => ({
        messages: [...prev.messages, { role: "user", content: text }],
        title: prev.messages.length === 0 || prev.title === "New Chat"
          ? text.slice(0, 40) + (text.length > 40 ? "..." : "")
          : prev.title,
      }))
    }
    setLoading(true)
    setStreamingContent("")
    setStreamingCitations([])
    setRetrievalStatus("")

    try {
      const res = await fetch(`${API}/ask/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, session_id: sessionId, model, web_search: webSearch, structured: true }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = "", fullAnswer = "", citations = [], isDone = false
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split("\n\n")
        buffer = events.pop() ?? ""
        for (const event of events) {
          const line = event.split("\n").find(l => l.startsWith("data: "))
          if (!line) continue
          let data
          try { data = JSON.parse(line.slice(6)) } catch { continue }
          if (data.type === "status") {
            setRetrievalStatus(data.message)
          } else if (data.type === "chunk") {
            fullAnswer += data.content
            setStreamingContent(fullAnswer)
          } else if (data.type === "metadata") {
            citations = data.citations || []
            setStreamingCitations(citations)
          } else if (data.type === "done") {
            isDone = true
            updateSession(sessionId, (prev) => ({
              messages: [...prev.messages, { role: "assistant", content: fullAnswer, citations }],
            }))
            setStreamingContent("")
            setStreamingCitations([])
            setRetrievalStatus("")
          } else if (data.type === "error") {
            throw new Error(data.message)
          }
        }
      }
      // fallback: if stream ended without a done event, still commit the answer
      if (!isDone && fullAnswer) {
        updateSession(sessionId, (prev) => ({
          messages: [...prev.messages, { role: "assistant", content: fullAnswer, citations }],
        }))
        setStreamingContent("")
        setStreamingCitations([])
        setRetrievalStatus("")
      }
    } catch (err) {
      setStreamingContent("")
      setStreamingCitations([])
      setRetrievalStatus("")
      updateSession(sessionId, (prev) => ({
        messages: [...prev.messages, { role: "assistant", content: `Error: ${err.message}` }],
      }))
    }
    setLoading(false)
    setStreamingContent("")
    setStreamingCitations([])
    setRetrievalStatus("")
  }, [model, webSearch, updateSession])

  const uploadFile = useCallback(async (file) => {
    if (!file) return
    setUploading(true)
    setUploadProgress("Uploading file...")
    const formData = new FormData()
    formData.append("file", file)
    try {
      setUploadProgress("Processing & embedding document...")
      const res = await axios.post(`${API}/upload?session_id=${current.id}`, formData)
      if (res.data.status === "success") {
        setUploading(false)
        setUploadProgress("")
        updateSession(current.id, (prev) => ({
          uploadedFile: file.name,
          title: prev.documents.length === 0 ? file.name.replace(/\.[^.]+$/, "") : prev.title,
          documents: prev.documents.includes(file.name) ? prev.documents : [...prev.documents, file.name],
          messages: [...prev.messages, {
            role: "assistant",
            content: `✅ **${file.name}** is ready (${res.data.chunks} chunks indexed).\n\n**What would you like to know about this document?**`,
          }],
        }))
        return
      }
    } catch {
      updateSession(current.id, { messages: [{ role: "system", content: "Upload failed. Backend not running." }] })
    }
    setUploading(false)
    setUploadProgress("")
  }, [current.id, updateSession])

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || loading) return
    setInput("")
    await streamQuestion(text, current.id)
  }, [current.id, loading, streamQuestion])

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input) }
  }

  const handleDeleteDoc = async (filename) => {
    try {
      await axios.post(`${API}/documents/delete`, { session_id: current.id, filename })
      updateSession(current.id, (prev) => ({
        documents: prev.documents.filter((d) => d !== filename),
        uploadedFile: prev.uploadedFile === filename ? null : prev.uploadedFile,
      }))
    } catch {}
  }

  const handleClear = async () => {
    try { await axios.post(`${API}/session/clear`, null, { params: { session_id: current.id } }) } catch {}
    updateSession(current.id, { messages: [], uploadedFile: null })
  }

  const exportChat = () => {
    const lines = current.messages.map((m) => {
      const role = m.role === "user" ? "**You**" : "**Assistant**"
      return `${role}\n${m.content}\n`
    })
    const blob = new Blob([lines.join("\n---\n\n")], { type: "text/markdown" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${current.title || "chat"}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const isLanding = current.messages.length === 0 && !streamingContent

  return (
    <div className="app">
      <main className="main">
        {/* Topbar */}
        <header className="topbar">
          <button className="topbar-sidebar-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
          <div className="topbar-center">
            {current.uploadedFile && <span className="topbar-file">📎 {current.uploadedFile}</span>}
          </div>
          <div className="topbar-right">
            {current.documents.length > 1 && (
              <label className="topbar-toggle" title="Search all documents">
                <input type="checkbox" checked={searchAllDocs} onChange={() => setSearchAllDocs(!searchAllDocs)} />
                <span title={searchAllDocs ? "All docs" : "Active doc"}>📚</span>
              </label>
            )}
            <div className="topbar-model">
              <select value={model} onChange={(e) => setModel(e.target.value)}>
                {Object.entries(models).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <label className="topbar-toggle" title="Web search">
              <input type="checkbox" checked={webSearch} onChange={() => setWebSearch(!webSearch)} />
              <span>🌐</span>
            </label>
            {current.messages.length > 0 && (
              <button className="topbar-clear-btn" onClick={exportChat} title="Export chat">⬇</button>
            )}
            <button className="topbar-clear-btn" onClick={handleClear} title="Clear chat">🗑</button>
          </div>
        </header>

        {/* Chat dropdown */}
        {sidebarOpen && (
          <>
            <div className="chat-dropdown">
              <div className="chat-dropdown-header">
                <span className="chat-dropdown-title">Chats</span>
                <button className="new-chat-btn-sm" onClick={() => { newChat(); setSidebarOpen(false) }}>✦ New Chat</button>
              </div>
              <ul className="chat-dropdown-list">
                {[...sessions].reverse().filter((s) => s.messages.length > 0 || s.id === currentId).map((s) => (
                  <li key={s.id} className={`chat-dropdown-item ${s.id === current.id ? "active" : ""}`}
                    onClick={() => { switchSession(s.id); setSidebarOpen(false) }}>
                    <span>💬</span>
                    <div className="chat-dropdown-info">
                      <span className="chat-dropdown-title-text">{s.title}</span>
                      <span className="chat-dropdown-msgs">{s.messages.filter((m) => m.role !== "system").length} messages</span>
                    </div>
                  </li>
                ))}
                {sessions.filter((s) => s.messages.length > 0).length === 0 && (
                  <li className="chat-dropdown-empty">No past chats</li>
                )}
              </ul>
            </div>
            <div className="chat-dropdown-overlay" onClick={() => setSidebarOpen(false)} />
          </>
        )}

        {/* Content */}
        <div className="content" ref={contentRef} onScroll={handleScroll}>
          {isLanding ? (
            <div className="landing">
              <div className="landing-icon">✦</div>
              <h1 className="landing-title">What would you like to know?</h1>
              <p className="landing-sub">Upload a document and ask anything about it</p>
            </div>
          ) : (
            <div className="messages">
              {current.messages.map((msg, i) => (
                <div key={i} className={`msg msg-${msg.role}`}>
                  <div className="msg-label">
                    {msg.role === "user" ? "You" : msg.role === "assistant" ? "Assistant" : "System"}
                  </div>
                  <div className="msg-bubble">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    {msg.citations?.length > 0 && (
                      <div className="citations">
                        <span className="citations-label">📄 Sources:</span>
                        {msg.citations.map((c, j) => (
                          <div key={j} className="citation-wrapper">
                            <span
                              className={`citation-chip ${expandedCitation === `${i}-${j}` ? "expanded" : ""}`}
                              onClick={() => setExpandedCitation(expandedCitation === `${i}-${j}` ? null : `${i}-${j}`)}
                            >
                              [{c.ref}] {c.filename} — chunk #{c.chunk_index}
                              {c.confidence != null && (
                                <span className={`confidence-badge ${c.confidence >= 70 ? "high" : c.confidence >= 40 ? "mid" : "low"}`}>
                                  {c.confidence}%
                                </span>
                              )}
                            </span>
                            {expandedCitation === `${i}-${j}` && (
                              <div className="citation-preview">
                                <p>{c.text_preview}...</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {retrievalStatus && (
                <div className="retrieval-status">
                  <span className="retrieval-dot" />
                  {retrievalStatus}
                </div>
              )}

              {streamingContent && (
                <div className="msg msg-assistant">
                  <div className="msg-label">Assistant</div>
                  <div className="msg-bubble streaming-bubble">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
                    {streamingCitations.length > 0 && (
                      <div className="citations">
                        <span className="citations-label">📄 Sources:</span>
                        {streamingCitations.map((c, j) => (
                          <span key={j} className="citation-chip">
                            [{c.ref}] {c.filename} — chunk #{c.chunk_index}
                            {c.confidence != null && (
                              <span className={`confidence-badge ${c.confidence >= 70 ? "high" : c.confidence >= 40 ? "mid" : "low"}`}>
                                {c.confidence}%
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    )}
                    <span className="cursor">|</span>
                  </div>
                </div>
              )}

              {loading && !streamingContent && !retrievalStatus && (
                <div className="msg msg-assistant">
                  <div className="msg-label">Assistant</div>
                  <div className="msg-bubble">
                    <div className="typing"><span /><span /><span /></div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-container">
            <button className="attach-btn" onClick={() => fileInputRef.current?.click()} title="Attach file">+</button>
            <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx,.csv,.json,.md,.html"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadFile(f); e.target.value = "" }}
              style={{ display: "none" }} />
            <textarea className="input-field" value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={current.uploadedFile ? "Ask about the document..." : "Upload a document to get started..."}
              rows={1} disabled={loading} />
            <button className="send-button" onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>→</button>
          </div>
          {uploading && <div className="input-status">⏳ {uploadProgress}</div>}
          {!uploading && current.uploadedFile && (
            <div className="input-status">
              📎 {current.uploadedFile}
              {current.documents.length > 1 && (
                <span className="search-scope-badge">{searchAllDocs ? "🔍 All docs" : "🔍 Active doc"}</span>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
