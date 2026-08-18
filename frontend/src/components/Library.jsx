export default function Library({ documents }) {
  if (documents.length === 0) {
    return <p className="empty">No documents yet — upload a PDF to get started.</p>;
  }
  return (
    <ul className="library">
      {documents.map((doc) => (
        <li key={doc.id}>
          <div className="doc-card" title={doc.error ?? doc.filename}>
            <span className="doc-name">{doc.filename}</span>
            <span className="doc-meta">
              {doc.page_count} page{doc.page_count === 1 ? '' : 's'} · {new Date(doc.upload_date).toLocaleDateString()}
            </span>
            {doc.summary && <p className="doc-summary">{doc.summary}</p>}
            <span className={`badge ${doc.status}`}>{doc.status}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
