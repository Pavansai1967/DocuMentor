import { useState } from 'react';
import { uploadPdf } from '../api';

const STATUS_LABELS = {
  uploading: 'Uploading...',
  processing: 'Wait, index is building',
  extracting: 'Extracting text...',
  embedding: 'Generating embeddings...',
  ready: 'Ready to chat',
  failed: 'Failed',
};

export default function Upload({ onUploaded }) {
  const [items, setItems] = useState([]);
  const [dragging, setDragging] = useState(false);

  async function handleFiles(files) {
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setItems((prev) => [...prev, { name: file.name, status: 'failed', error: 'Not a PDF' }]);
        continue;
      }
      const id = crypto.randomUUID();
      setItems((prev) => [...prev, { id, name: file.name, status: 'uploading' }]);
      try {
        await uploadPdf(file);
        setItems((prev) => prev.map((it) => (it.id === id ? { ...it, status: 'ready' } : it)));
        onUploaded?.();
      } catch (err) {
        setItems((prev) => prev.map((it) => (it.id === id ? { ...it, status: 'failed', error: err.message } : it)));
      }
    }
  }

  return (
    <section className="upload">
      <h2>Upload a PDF</h2>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles([...e.dataTransfer.files]); }}
        onClick={() => document.getElementById('file-input')?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter') document.getElementById('file-input')?.click(); }}
      >
        <input
          id="file-input"
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => handleFiles([...e.target.files])}
        />
        <p>Drag &amp; drop PDFs here, or click to browse</p>
      </div>
      {items.length > 0 && (
        <ul className="upload-items">
          {items.map((it) => (
            <li key={it.id}>
              <span>{it.name}</span>
              <em className={`status ${it.status}`}>{it.status === 'ready' ? 'Ready to chat' : it.status === 'failed' ? it.error : STATUS_LABELS[it.status]}</em>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
