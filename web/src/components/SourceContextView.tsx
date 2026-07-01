export function SourceContextView({ context }: { context: Record<string, unknown> }) {
  const entries = Object.entries(context);
  if (entries.length === 0) {
    return <p className="text-sm text-text-muted">No source context.</p>;
  }
  return (
    <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded-lg bg-surface-washed p-3">
          <dt className="eyebrow text-text-muted">{key.replace(/_/g, " ")}</dt>
          <dd className="mt-0.5 break-words text-sm text-text">
            {typeof value === "object" ? (
              <pre className="overflow-x-auto text-xs">{JSON.stringify(value, null, 2)}</pre>
            ) : (
              String(value)
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}
