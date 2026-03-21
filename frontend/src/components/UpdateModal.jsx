const riskStyles = {
  High: "bg-red-100 text-danger",
  Medium: "bg-amber-100 text-warning",
  Low: "bg-emerald-100 text-safe",
};

export default function UpdateModal({ update, onClose }) {
  if (!update) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/35 px-4" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-soft"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="font-heading text-xl font-semibold text-slate-900">{update.title}</h2>
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${riskStyles[update.risk] || "bg-slate-100 text-slate-700"}`}>
            {update.risk}
          </span>
        </div>
        <p className="mb-4 text-sm text-slate-500">{new Date(update.timestamp).toLocaleString()}</p>
        <p className="mb-6 text-sm leading-relaxed text-slate-700">{update.summary}</p>
        <h3 className="mb-2 font-heading text-sm font-semibold uppercase tracking-wide text-slate-500">Action Steps</h3>
        <ul className="space-y-2 text-sm text-slate-700">
          {update.action.map((step) => (
            <li key={step} className="rounded-xl bg-slate-50 px-3 py-2">
              {step}
            </li>
          ))}
        </ul>
        <div className="mt-6 text-right">
          <button
            type="button"
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
