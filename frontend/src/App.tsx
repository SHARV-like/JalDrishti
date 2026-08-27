import { useEffect, useState } from "react";
import { getWatersheds, type Watershed } from "./api";

const cards = [
  ["GeoProof", "Ready for transparent location checks", "Verify"],
  ["Satellite change", "Prepared NDVI / NDWI demo assets", "Compare"],
  ["Next action", "Explainable MCDA recommendation", "Review"]
];

export default function App() {
  const [watersheds, setWatersheds] = useState<Watershed[]>([]);
  const [status, setStatus] = useState("Loading demo watershed…");

  useEffect(() => {
    getWatersheds().then((data) => { setWatersheds(data); setStatus("Prepared demo data"); }).catch(() => setStatus("API unavailable — start the FastAPI service."));
  }, []);

  return <main className="min-h-screen bg-slate-950 text-slate-100"><section className="mx-auto max-w-6xl px-6 py-16">
    <p className="text-sm font-semibold tracking-[0.2em] text-cyan-400">JALDRISHTI AI · MVP</p>
    <h1 className="mt-4 text-5xl font-bold tracking-tight">Evidence to action for watershed development.</h1>
    <p className="mt-5 max-w-3xl text-lg text-slate-300">A traceable dashboard for field evidence, geospatial verification, satellite indicators, risk, and next-best interventions.</p>
    <div className="mt-10 rounded-2xl border border-slate-700 bg-slate-900 p-6"><div className="flex items-center justify-between gap-4"><div><h2 className="text-xl font-semibold">Watershed explorer</h2><p className="mt-1 text-slate-400">{status}</p></div><span className="rounded-full bg-amber-400/15 px-3 py-1 text-sm text-amber-300">demo</span></div>
      {watersheds.length ? <ul className="mt-5 divide-y divide-slate-800">{watersheds.map((item) => <li className="py-4" key={item.id}><strong>{item.name}</strong><span className="ml-3 text-sm text-slate-400">Source: {item.provenance.source_name}</span></li>)}</ul> : <p className="mt-5 text-slate-500">The map and layer controls will use the prepared GeoJSON here.</p>}
    </div>
    <section className="mt-8 grid gap-5 md:grid-cols-3">{cards.map(([title, body, action]) => <article className="rounded-2xl bg-slate-900 p-6" key={title}><p className="font-semibold text-cyan-300">{title}</p><p className="mt-3 min-h-12 text-slate-400">{body}</p><button className="mt-6 rounded-lg border border-cyan-400 px-4 py-2 text-sm font-semibold text-cyan-300">{action}</button></article>)}</section>
  </section></main>;
}
