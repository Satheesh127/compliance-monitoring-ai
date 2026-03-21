const riskStyles = {
  High: "bg-red-100 text-danger",
  Medium: "bg-amber-100 text-warning",
  Low: "bg-emerald-100 text-safe",
};

export default function UpdateCard({ update, onClick }) {
  const riskClass = riskStyles[update.risk] || "bg-slate-100 text-slate-700";

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-soft transition hover:-translate-y-0.5"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="font-heading text-lg font-semibold text-slate-900">{update.title}</h3>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${riskClass}`}>{update.risk}</span>
      </div>
      <p className="line-clamp-3 text-sm text-slate-600">{update.summary}</p>
      <p className="mt-4 text-xs text-slate-400">{new Date(update.timestamp).toLocaleString()}</p>
    </button>
  );
}
