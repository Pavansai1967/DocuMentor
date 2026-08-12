import { useEffect, useRef, useState } from 'react';
import { listDocuments } from './api';
import Upload from './components/Upload';
import Library from './components/Library';
import Chat from './components/Chat';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selected, setSelected] = useState(null);
  const timer = useRef(null);

  async function refresh() {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setSelected((cur) => (cur ? docs.find((d) => d.id === cur.id) ?? null : cur));
    } catch {
      setDocuments([]);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (documents.some((d) => d.status === 'processing')) {
      if (!timer.current) {
        timer.current = setInterval(refresh, 2000);
      }
      return () => {
        clearInterval(timer.current);
        timer.current = null;
      };
    }
  }, [documents]);

  return (
    <div className="app">
      <header className="topbar">
        <h1>DocuMentor</h1>
      </header>
      <main className="layout">
        <aside className="panel library-panel">
          <Upload onUploaded={refresh} />
          <h2>Your documents</h2>
          <Library documents={documents} selectedId={selected?.id} onSelect={setSelected} />
        </aside>
        <section className="panel chat-panel">
          <Chat document={selected} />
        </section>
      </main>
    </div>
  );
}
