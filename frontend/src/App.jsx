import { useState, useRef, useEffect } from 'react'
import { sendMessage } from './api'
import './index.css'

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! Please paste or type a job description, and I\'ll analyze it for gender bias in language.'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setError(null)

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const response = await sendMessage(userMessage, conversationId)
      
      // Update conversation ID if new
      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id)
      }

      // Add assistant response
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.response 
      }])
    } catch (err) {
      setError('Failed to send message. Please check your connection and try again.')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="app">
      <div className="header">
        <h1>Job Description Bias Analyzer</h1>
        <p>AI-powered analysis for inclusive hiring</p>
      </div>

      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-bubble">{msg.content}</div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant">
            <div className="loading">
              <span>Analyzing</span>
              <div className="loading-dots">
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error">{error}</div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <form onSubmit={handleSubmit} className="input-container">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste or type a job description here..."
            disabled={isLoading}
            rows={1}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
