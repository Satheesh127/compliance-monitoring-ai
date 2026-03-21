import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const location = useLocation();
  const onChatPage = location.pathname === "/chatbot";

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/70 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <div>
          <h1 className="font-heading text-xl font-semibold tracking-tight text-ink sm:text-2xl">
            Compliance Monitoring AI
          </h1>
          <p className="text-sm text-slate-500">Real-time regulation intelligence</p>
        </div>
        <Link
          to={onChatPage ? "/" : "/chatbot"}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-soft transition hover:-translate-y-0.5 hover:bg-slate-800"
        >
          {onChatPage ? "Dashboard" : "Ask AI"}
        </Link>
      </div>
    </header>
  );
}
