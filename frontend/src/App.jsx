import { useEffect, useRef, useState } from 'react';
import { listDocuments } from './api';
import Upload from './components/Upload';
import Library from './components/Library';
import Chat from './components/Chat';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const timer = useRef(null);

  async function refresh() {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
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
          <Library documents={documents} />
        </aside>
        <section className="panel chat-panel">
          <Chat documents={documents} />
        </section>
      </main>
    </div>
  );
}
