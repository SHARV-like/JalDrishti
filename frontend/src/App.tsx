import { useEffect, useState } from "react";
import { DataAssumptions } from "./components/DataAssumptions";
import { DEMO_EVIDENCE, EvidenceUpload, type EvidenceResult } from "./components/EvidenceUpload";
import { MetricCard } from "./components/MetricCard";
import { OperationsPanel } from "./components/OperationsPanel";
import { SatelliteImpact } from "./components/SatelliteImpact";
import { WatershedMap } from "./components/WatershedMap";

type Section = "overview" | "evidence" | "satellite" | "risk" | "reports";
type Theme = "light" | "dark";
const navigation: { id: Section; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "▦" }, { id: "evidence", label: "Field Evidence", icon: "⌁" },
  { id: "satellite", label: "Satellite Analysis", icon: "◫" }, { id: "risk", label: "Risk Map", icon: "△" }, { id: "reports", label: "Reports", icon: "▤" },
];
function getInitialTheme(): Theme { const stored = localStorage.getItem("jaldirshti-theme"); if (stored === "light" || stored === "dark") return stored; return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"; }

export default function App() {
  const [evidence, setEvidence] = useState<EvidenceResult | null>(null);
  const [scenarioVersion, setScenarioVersion] = useState(0);
  const [section, setSection] = useState<Section>("overview");
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("jaldirshti-theme", theme); }, [theme]);
  function loadDemoScenario() { setEvidence(DEMO_EVIDENCE); setScenarioVersion((version) => version + 1); setSection("overview"); }
  const sectionTitle = navigation.find((item) => item.id === section)?.label ?? "Overview";
  return <main className="app-frame"><header className="topbar"><div className="brand"><span className="brand-mark">JD</span><div><strong>JalDrishti AI</strong><small>Watershed operations</small></div></div><div className="topbar-context"><span className="watershed-select">Illustrative Demo Watershed <b>⌄</b></span><button className="theme-toggle" type="button" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}>{theme === "light" ? "◐ Dark" : "◑ Light"}</button><button className="user-menu" type="button" aria-label="Open demo user menu">Demo user <b>⌄</b></button></div></header><div className="workspace"><nav className="side-nav" aria-label="Dashboard navigation">{navigation.map((item) => <button key={item.id} type="button" className={section === item.id ? "active" : ""} onClick={() => setSection(item.id)}><span aria-hidden="true">{item.icon}</span><span>{item.label}</span></button>)}<div className="nav-footer"><span className="demo-dot" />Pilot/demo data</div></nav><section className="workspace-main"><div className="content-heading"><div><p className="eyebrow">{sectionTitle.toUpperCase()}</p><h1>{section === "overview" ? "Watershed overview" : sectionTitle}</h1></div><button className="scenario-button" type="button" onClick={loadDemoScenario}>Load demo scenario</button></div><section className="metrics operations-metrics" aria-label="Watershed summary metrics"><MetricCard label="Verified interventions" value="4" detail="of 5 pilot sites" accent="emerald" /><MetricCard label="High-risk zones" value="1" detail="requires field review" accent="amber" /><MetricCard label="Average impact" value="83" detail="weighted pilot score" accent="cyan" /><MetricCard label="Watershed area" value="38.6 ha" detail="illustrative boundary" accent="violet" /></section>{section === "evidence" ? <><OperationsPanel /><EvidenceUpload onEvidenceUploaded={setEvidence} demoScenarioVersion={scenarioVersion} /></> : null}{section === "satellite" ? <SatelliteImpact evidence={evidence} /> : null}{section === "reports" ? <section className="section-note"><strong>Impact reports</strong><span>Select an intervention marker on the map, then use the report action in the site drawer. Reports are generated locally from curated pilot data.</span></section> : null}{section === "risk" ? <section className="section-note"><strong>Residual risk map</strong><span>Select a coloured risk zone to inspect conditions, suitability scores, and the transparent recommended next action.</span></section> : null}<WatershedMap evidence={evidence} demoScenarioVersion={scenarioVersion} />{section === "overview" ? <DataAssumptions /> : null}</section></div></main>;
}
