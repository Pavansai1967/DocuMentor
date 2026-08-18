export default function AgentSteps({ trace }) {
  if (!trace || trace.length === 0) return null;
  return (
    <div className="agent-steps">
      <details>
        <summary>Agent steps</summary>
        <ul>
          {trace.map((step, i) => (
            <li key={i}>
              <strong>{step.step}</strong>
              {step.step === 'plan' && step.sub_queries && (
                <span> — planned {step.sub_queries.length} search{step.sub_queries.length !== 1 ? 'es' : ''}</span>
              )}
              {step.step === 'retrieve' && (
                <span> — found {step.chunks_found} chunks from {step.queries_run} queries</span>
              )}
              {step.step === 'evaluate' && (
                <span> — {step.sufficient ? 'sufficient evidence' : `insufficient (iteration ${step.iteration_count})`}</span>
              )}
              {step.step === 'answer' && (
                <span> — answered after {step.iteration_count} iteration{step.iteration_count !== 1 ? 's' : ''}</span>
              )}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
