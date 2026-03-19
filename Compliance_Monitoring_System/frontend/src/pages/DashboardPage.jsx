import { useEffect, useMemo, useRef, useState } from "react";
import { fetchStats, fetchUpdates } from "../api/client";
import Navbar from "../components/Navbar";
import UpdateCard from "../components/UpdateCard";
import UpdateModal from "../components/UpdateModal";

function StatCard({ label, value }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <p className="text-sm text-slate-500">{label}</p>
      <h2 className="mt-2 font-heading text-3xl font-semibold text-slate-900">{value}</h2>
    </article>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState({ total_updates: 0, high_risk_count: 0, regions: [] });
  const [updates, setUpdates] = useState([]);
  const [activeUpdate, setActiveUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const isMountedRef = useRef(false);
  const isFetchingRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;

    async function loadData({ initial = false } = {}) {
      if (isFetchingRef.current) {
        return;
      }

      isFetchingRef.current = true;
      try {
        const [statsData, updatesData] = await Promise.all([fetchStats(), fetchUpdates()]);
        if (!isMountedRef.current) {
          return;
        }
        setStats(statsData);
        setUpdates(updatesData);
      } catch (error) {
        console.error("Failed to refresh dashboard data:", error);
      } finally {
        isFetchingRef.current = false;
        if (initial && isMountedRef.current) {
          setLoading(false);
        }
      }
    }

    loadData({ initial: true });

    const intervalId = setInterval(() => {
      loadData();
    }, 5000);

    return () => {
      isMountedRef.current = false;
      clearInterval(intervalId);
    };
  }, []);

  const regionCount = useMemo(() => (stats.regions || []).length, [stats.regions]);

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard label="Total Updates" value={stats.total_updates} />
          <StatCard label="High Risk Alerts" value={stats.high_risk_count} />
          <StatCard label="Regions" value={regionCount} />
        </section>

        <section className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-heading text-xl font-semibold text-slate-900">Recent Updates</h2>
            {loading && <span className="text-sm text-slate-500">Loading...</span>}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {updates.map((update, index) => (
              <div key={update.id} className="animate-rise" style={{ animationDelay: `${index * 40}ms` }}>
                <UpdateCard update={update} onClick={() => setActiveUpdate(update)} />
              </div>
            ))}
          </div>

          {!loading && updates.length === 0 && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              No updates captured yet. The monitor will populate this page after detecting regulation changes.
            </div>
          )}
        </section>
      </main>

      <UpdateModal update={activeUpdate} onClose={() => setActiveUpdate(null)} />
    </div>
  );
}
