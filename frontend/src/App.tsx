import { useState } from "react";
import { DataAssumptions } from "./components/DataAssumptions";
import { DemoFlow } from "./components/DemoFlow";
import { DEMO_EVIDENCE, EvidenceUpload, type EvidenceResult } from "./components/EvidenceUpload";
import { MetricCard } from "./components/MetricCard";
import { SatelliteImpact } from "./components/SatelliteImpact";
import { WatershedMap } from "./components/WatershedMap";

export default function App() {
  const [evidence, setEvidence] = useState<EvidenceResult | null>(null);
  const [scenarioVersion, setScenarioVersion] = useState(0);
  function loadDemoScenario() { setEvidence(DEMO_EVIDENCE); setScenarioVersion((version) => version + 1); }
  return <main><section className="dashboard"><header className="hero"><div><p className="eyebrow">WATERSHED INTELLIGENCE · MVP</p><h1>JalDrishti AI</h1><p>Verify interventions, understand risk, and prioritise water security with traceable evidence.</p></div><div className="hero-actions"><div className="hero-status"><span />Prepared demonstration · v0.1</div><button className="demo-load-button" onClick={loadDemoScenario}>Load Demo Scenario</button></div></header>
    <section className="metrics" aria-label="Watershed dashboard metrics"><MetricCard label="Verified Interventions" value="4" detail="of 5 prepared demo sites" accent="emerald" /><MetricCard label="High-Risk Zones" value="1" detail="requires field review" accent="amber" /><MetricCard label="Average Impact Score" value="83" detail="out of 100 · demo estimate" accent="cyan" /><MetricCard label="Watershed Area" value="38.6 ha" detail="illustrative boundary" accent="violet" /></section>
    <DemoFlow loaded={scenarioVersion > 0} />
    <EvidenceUpload onEvidenceUploaded={setEvidence} demoScenarioVersion={scenarioVersion} />
    <SatelliteImpact evidence={evidence} />
    <WatershedMap evidence={evidence} demoScenarioVersion={scenarioVersion} />
    <DataAssumptions />
  </section></main>;
}
