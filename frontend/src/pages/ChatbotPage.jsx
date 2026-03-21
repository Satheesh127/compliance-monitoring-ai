import { useEffect, useRef, useState } from "react";
import { askChatbot } from "../api/client";
import ChatMessage from "../components/ChatMessage";
import Navbar from "../components/Navbar";

export default function ChatbotPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Summary: Ask a question about regulation updates.\nRisk: Unknown\nAction:\n- Provide a focused compliance question\n- I will answer from stored updates only\nSource: N/A",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(event) {
    event.preventDefault();
    const value = question.trim();
    if (!value || loading) {
      return;
    }

    setMessages((prev) => [...prev, { role: "user", text: value }]);
    setQuestion("");
    setLoading(true);

    try {
      const data = await askChatbot(value);
      setMessages((prev) => [...prev, { role: "assistant", text: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Summary: Unable to fetch response.\nRisk: Unknown\nAction:\n- Verify backend is running\n- Try again\nSource: N/A",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto flex h-[calc(100vh-85px)] w-full max-w-5xl flex-col px-4 py-6 sm:px-6">
        <section className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
          {messages.map((item, index) => (
            <ChatMessage key={`${item.role}-${index}`} role={item.role} text={item.text} />
          ))}
          {loading && <p className="text-sm text-slate-500">AI is thinking...</p>}
          <div ref={scrollRef} />
        </section>

        <form onSubmit={handleSend} className="mt-4 flex gap-3">
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about latest compliance updates"
            className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-0 focus:border-slate-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
