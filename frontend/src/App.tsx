import { MetricCard } from "./components/MetricCard";
import { WatershedMap } from "./components/WatershedMap";

export default function App() {
  const [evidence, setEvidence] = useState<EvidenceResult | null>(null);
  return <main><section className="dashboard"><header className="hero"><div><p className="eyebrow">WATERSHED INTELLIGENCE · MVP</p><h1>JalDrishti AI</h1><p>Verify interventions, understand risk, and prioritise water security with traceable evidence.</p></div><div className="hero-status"><span />Prepared demonstration · v0.1</div></header>
    <section className="metrics" aria-label="Watershed dashboard metrics"><MetricCard label="Verified Interventions" value="4" detail="of 5 prepared demo sites" accent="emerald" /><MetricCard label="High-Risk Zones" value="1" detail="requires field review" accent="amber" /><MetricCard label="Average Impact Score" value="83" detail="out of 100 · demo estimate" accent="cyan" /><MetricCard label="Watershed Area" value="38.6 ha" detail="illustrative boundary" accent="violet" /></section>
    <EvidenceUpload onEvidenceUploaded={setEvidence} />
    <WatershedMap evidence={evidence} />
  </section></main>;
}
import { useState } from "react";
import { EvidenceUpload, type EvidenceResult } from "./components/EvidenceUpload";
