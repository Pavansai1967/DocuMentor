import { useEffect, useRef, useState } from 'react';
import { streamChat } from '../api';
import Sources from './Sources';

export default function Chat({ document }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    setMessages([]);
    setInput('');
  }, [document?.id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const ready = document?.status === 'ready';

  async function ask() {
    const question = input.trim();
    if (!question || streaming) return;
    setInput('');
    setStreaming(true);
    setMessages((prev) => [...prev, { role: 'user', text: question }]);
    setMessages((prev) => [...prev, { role: 'assistant', text: '' }]);

    const controller = new AbortController();
    try {
      await streamChat({
        document_id: document.id,
        question,
        signal: controller.signal,
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
        {document ? <h2>{document.filename}</h2> : <h2>Select a document to chat</h2>}
        {document && <span className={`badge ${document.status}`}>{document.status}</span>}
      </header>

      <div className="messages">
        {messages.length === 0 && <p className="empty">Ask a question about this document. Answers are stateless — each question is answered independently.</p>}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.text || (m.error ? '—' : '…')}
            {m.error && <p className="error">Error: {m.error}</p>}
            {m.role === 'assistant' && <Sources sources={m.sources} />}
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
          placeholder={ready ? 'Ask about this document…' : 'Upload a PDF and wait for it to be ready'}
          disabled={!ready || streaming}
        />
        <button type="submit" disabled={!ready || streaming || !input.trim()}>
          {streaming ? '…' : 'Ask'}
        </button>
      </form>
    </section>
  );
}
