export default function ChatMessage({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-soft sm:max-w-[70%] ${
          isUser ? "bg-slate-900 text-white" : "bg-white text-slate-800"
        }`}
      >
        <pre className="whitespace-pre-wrap font-body">{text}</pre>
      </div>
    </div>
  );
}
