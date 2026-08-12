export default function Library({ documents, selectedId, onSelect }) {
  if (documents.length === 0) {
    return <p className="empty">No documents yet — upload a PDF to get started.</p>;
  }
  return (
    <ul className="library">
      {documents.map((doc) => (
        <li key={doc.id}>
          <button
            type="button"
            className={doc.id === selectedId ? 'selected' : ''}
            onClick={() => onSelect(doc)}
            title={doc.error ?? doc.filename}
          >
            <span className="doc-name">{doc.filename}</span>
            <span className="doc-meta">
              {doc.page_count} page{doc.page_count === 1 ? '' : 's'} · {new Date(doc.upload_date).toLocaleDateString()}
            </span>
            <span className={`badge ${doc.status}`}>{doc.status}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
