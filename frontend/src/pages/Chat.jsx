import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Send, LogOut, Zap, ChevronDown } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const API = import.meta.env.VITE_API_URL || ''

export default function Chat({ token, onLogout }) {
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [usage, setUsage] = useState(null)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    fetchModels()
    fetchUsage()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchModels = async () => {
    try {
      const { data } = await axios.get(`${API}/api/models/`, { headers })
      setModels(data)
      if (data.length > 0) setSelectedModel(data[0])
    } catch (e) {
      console.error(e)
    }
  }

  const fetchUsage = async () => {
    try {
      const { data } = await axios.get(`${API}/api/usage/my`, { headers })
      setUsage(data)
    } catch (e) {}
  }

  const sendMessage = async () => {
    if (!input.trim() || loading || !selectedModel) return

    const userMsg = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    const assistantMsg = { role: 'assistant', content: '' }
    setMessages([...newMessages, assistantMsg])

    try {
      const response = await fetch(`${API}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          model_id: selectedModel.id,
          messages: newMessages,
          temperature: 0.7,
          max_tokens: 2048,
        }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          const data = JSON.parse(line.slice(6))
          if (data.content) {
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: updated[updated.length - 1].content + data.content
              }
              return updated
            })
          }
          if (data.done) {
            fetchUsage()
          }
          if (data.error) {
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1].content = `Error: ${data.error}`
              return updated
            })
          }
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1].content = 'Connection error. Please try again.'
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => setMessages([])

  return (
    <div className="flex flex-col h-screen bg-gray-950">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          <span className="font-bold text-white">AI Playground</span>
        </div>

        {/* Model selector */}
        <div className="flex items-center gap-2">
          <select
            value={selectedModel?.id || ''}
            onChange={e => setSelectedModel(models.find(m => m.id === e.target.value))}
            className="bg-gray-800 text-white text-sm rounded-lg px-3 py-1.5 border border-gray-700 focus:outline-none focus:border-blue-500"
          >
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.display_name}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          {usage && (
            <span className="text-xs text-gray-400">
              {usage.today}/{usage.daily_limit} today
            </span>
          )}
          <button onClick={clearChat} className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-800">
            Clear
          </button>
          <button onClick={onLogout} className="text-gray-400 hover:text-white">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Zap className="w-12 h-12 text-yellow-400 mb-4 opacity-50" />
            <h2 className="text-xl font-semibold text-gray-300 mb-2">AI Playground</h2>
            <p className="text-gray-500 text-sm">Select a model and start chatting</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-100'
            }`}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{msg.content || (loading && i === messages.length - 1 ? '▋' : '')}</ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
        <div className="flex items-end gap-2 bg-gray-800 rounded-2xl px-4 py-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message... (Enter to send, Shift+Enter for newline)"
            rows={1}
            className="flex-1 bg-transparent text-white text-sm resize-none outline-none max-h-40 scrollbar-thin placeholder-gray-500 py-1"
            style={{ minHeight: '36px' }}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="p-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-xs text-gray-600 mt-2">AI can make mistakes. Verify important info.</p>
      </div>
    </div>
  )
}
