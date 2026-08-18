import { useEffect, useRef, useState } from 'react';
import { streamChat } from '../api';
import Sources from './Sources';
import AgentSteps from './AgentSteps';

export default function Chat({ documents }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const ready = documents.some((d) => d.status === 'ready');

  async function ask() {
    const question = input.trim();
    if (!question || streaming) return;
    setInput('');
    setStreaming(true);
    setMessages((prev) => [...prev, { role: 'user', text: question }]);
    setMessages((prev) => [...prev, { role: 'assistant', text: '' }]);

    try {
      await streamChat({
        question,
        onToken: (t) => setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { ...copy[copy.length - 1], text: copy[copy.length - 1].text + t };
          return copy;
        }),
        onSources: (sources) => setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { ...copy[copy.length - 1], sources };
          return copy;
        }),
        onTrace: (trace) => setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { ...copy[copy.length - 1], trace };
          return copy;
        }),
        onError: (err) => setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { ...copy[copy.length - 1], error: err.message };
          return copy;
        }),
      });
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { ...copy[copy.length - 1], error: err.message };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <section className="chat">
      <header className="chat-header">
        <h2>Chat with your documents</h2>
      </header>

      <div className="messages">
        {messages.length === 0 && <p className="empty">Ask a question about your documents. The agent will search across your entire library.</p>}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.text || (m.error ? '—' : '…')}
            {m.error && <p className="error">Error: {m.error}</p>}
            {m.role === 'assistant' && <Sources sources={m.sources} />}
            {m.role === 'assistant' && <AgentSteps trace={m.trace} />}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <form
        className="composer"
        onSubmit={(e) => { e.preventDefault(); ask(); }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={ready ? 'Ask about your documents…' : 'Upload a PDF and wait for it to be ready'}
          disabled={!ready || streaming}
        />
        <button type="submit" disabled={!ready || streaming || !input.trim()}>
          {streaming ? '…' : 'Ask'}
        </button>
      </form>
    </section>
  );
}
