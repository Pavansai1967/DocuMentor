export default function Sources({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="sources">
      <details>
        <summary>Sources</summary>
        <ul>
          {sources.map((s, i) => (
            <li key={i}>
              <span className="source-chip">{i + 1} · p. {s.page_number}</span>
              <details>
                <summary>Excerpt</summary>
                <p>{s.text}</p>
              </details>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
