import { useEffect, useMemo, useState } from "react";
import { CircleMarker, GeoJSON, MapContainer, Polyline, Popup, TileLayer } from "react-leaflet";
import type { Feature, FeatureCollection, Point, Polygon } from "geojson";
import "leaflet/dist/leaflet.css";
import type { EvidenceResult } from "./EvidenceUpload";

type InterventionProperties = { id: string; name?: string; intervention_type: string; status: string; impact_score: number; data_status: string };
type RiskConditions = { slope_deg: number; runoff_proxy: string; vegetation_condition: string; terrain_soil_proxy: string; distance_to_drainage_m: number };
type RiskProperties = { id: string; name: string; risk_level: "high" | "medium" | "low"; risk_score: number; conditions: RiskConditions; data_status: string };
type MapLayers = { watershed: FeatureCollection<Polygon>; interventions: FeatureCollection<Point, InterventionProperties>; riskZones: FeatureCollection<Polygon, RiskProperties> };
type Recommendation = { intervention: string; score: number; reasons: string[] };
type RecommendationResult = { recommendations: Recommendation[]; recommended_next_action: Recommendation; disclaimer: string };
type TimelineItem = [title: string, detail: string, state: "complete" | "pending" | "next"];
type SiteDetail = { completion_date: string; latest_evidence: { image: string; caption: string } | null; geoproof: { score: number | null; status: string }; impact_score: number | null; remaining_risk: string; timeline: TimelineItem[] };
type SiteDetails = { data_status: "demo"; source: string; sites: Record<string, SiteDetail> };

const demoCenter: [number, number] = [19.006, 73.008];
const riskColors = { high: "#ef4444", medium: "#f59e0b", low: "#22c55e" };

export function WatershedMap({ evidence }: { evidence: EvidenceResult | null }) {
  const [selected, setSelected] = useState<InterventionProperties | null>(null);
  const [layers, setLayers] = useState<MapLayers | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<RiskProperties | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [siteDetails, setSiteDetails] = useState<SiteDetails>({ data_status: "demo", source: "JalDrishti MVP curated pilot dataset", sites: {} });
  useEffect(() => {
    Promise.all([fetch("/geo/watersheds.geojson"), fetch("/geo/interventions.geojson"), fetch("/geo/risk-zones.geojson"), fetch("/geo/intervention-site-details.json")])
      .then(async ([watershed, interventionData, risks, details]) => {
        if (!watershed.ok || !interventionData.ok || !risks.ok || !details.ok) throw new Error("Demo layer load failed");
        setLayers({ watershed: await watershed.json(), interventions: await interventionData.json(), riskZones: await risks.json() });
        setSiteDetails(await details.json());
      }).catch(() => setLoadError(true));
  }, []);
  useEffect(() => {
    if (!selectedRisk) return;
    fetch(`http://localhost:8000/api/v1/risk-zones/${selectedRisk.id}/recommendations`).then((response) => response.ok ? response.json() : Promise.reject()).then((data: RecommendationResult) => setRecommendation(data)).catch(() => setRecommendation(null));
  }, [selectedRisk]);
  const selectedSummary = useMemo(() => selected ? `${selected.name ?? selected.intervention_type} selected` : "Select a marker for field details", [selected]);
  const selectedDetail = selected ? siteDetails.sites[selected.id] : null;

  return <section className="map-shell" aria-label="Watershed GIS map">
    <div className="map-header"><div><p className="eyebrow">GIS WATERSHED EXPLORER</p><h2>Illustrative Demo Watershed</h2><p className="map-subtitle">Prepared offline-friendly demo layers · not for field decisions</p></div><span className="demo-chip">DEMO DATA</span></div>
    <div className="map-grid"><div className="map-canvas"><MapContainer center={demoCenter} zoom={14} scrollWheelZoom className="leaflet-map" aria-label="Map of the illustrative demo watershed">
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {layers ? <><GeoJSON data={layers.watershed} style={{ color: "#0e7490", weight: 3, fillColor: "#67e8f9", fillOpacity: 0.13 }} />
      <GeoJSON data={layers.riskZones} style={(feature) => { const properties = feature?.properties as RiskProperties | undefined; const level = properties?.risk_level ?? "low"; return { color: riskColors[level], weight: selectedRisk?.id === properties?.id ? 4 : 2, fillColor: riskColors[level], fillOpacity: selectedRisk?.id === properties?.id ? 0.5 : 0.28 }; }} onEachFeature={(feature, layer) => { const properties = feature.properties as RiskProperties; layer.bindTooltip(`${properties.name} · ${properties.risk_score}/100`, { sticky: true }); layer.on({ click: () => setSelectedRisk(properties) }); }} />
      {layers.interventions.features.map((feature) => <CircleMarker key={feature.properties.id} center={[feature.geometry.coordinates[1], feature.geometry.coordinates[0]]} radius={8} pathOptions={{ color: feature.properties.intervention_type === "farm_pond" ? "#2563eb" : "#059669", fillColor: "#ffffff", fillOpacity: 1, weight: 4 }} eventHandlers={{ click: () => setSelected(feature.properties) }}><Popup><strong>{feature.properties.name ?? feature.properties.intervention_type}</strong><br />{feature.properties.intervention_type.replace(/_/g, " ")} · {feature.properties.status}<br /><small>Demo data</small></Popup></CircleMarker>)}</> : null}
      {evidence?.metadata.gps ? <CircleMarker center={[evidence.metadata.gps.latitude, evidence.metadata.gps.longitude]} radius={10} pathOptions={{ color: "#a855f7", fillColor: "#f5d0fe", fillOpacity: 1, weight: 4 }}><Popup><strong>Uploaded field evidence</strong><br />GPS extracted locally<br /><small>Not persisted</small></Popup></CircleMarker> : null}
      {evidence?.metadata.gps && evidence.geoproof.nearest_intervention ? <Polyline positions={[[evidence.metadata.gps.latitude, evidence.metadata.gps.longitude], [evidence.geoproof.nearest_intervention.latitude, evidence.geoproof.nearest_intervention.longitude]]} pathOptions={{ color: "#a855f7", weight: 3, dashArray: "7 7" }} /> : null}
    </MapContainer></div>
      <aside className="map-sidebar"><div className="selection-card site-panel"><p className="eyebrow">INTERVENTION SITE DETAILS</p><h3>{selected?.name ?? "Choose a marker"}</h3><p>{loadError ? "Demo layers could not load." : selectedSummary}</p>{selected && selectedDetail ? <><dl><div><dt>Type</dt><dd>{selected.intervention_type.replace(/_/g, " ")}</dd></div><div><dt>Status</dt><dd><span className={`site-status site-status--${selected.status}`}>{selected.status}</span></dd></div><div><dt>GPS</dt><dd>{selected.id === "demo-intervention-001" ? "19.0060, 73.0070" : layers?.interventions.features.find((item) => item.properties.id === selected.id)?.geometry.coordinates.slice().reverse().map((value) => value.toFixed(4)).join(", ")}</dd></div><div><dt>Completion</dt><dd>{selectedDetail.completion_date}</dd></div><div><dt>GeoProof</dt><dd>{selectedDetail.geoproof.score === null ? "Pending" : `${selectedDetail.geoproof.score}/100 · ${selectedDetail.geoproof.status}`}</dd></div><div><dt>Impact score</dt><dd>{selectedDetail.impact_score === null ? "Pending" : `${selectedDetail.impact_score}/100`}</dd></div><div><dt>Remaining risk</dt><dd>{selectedDetail.remaining_risk}</dd></div></dl>{selectedDetail.latest_evidence ? <figure className="site-evidence"><img src={selectedDetail.latest_evidence.image} alt={selectedDetail.latest_evidence.caption} /><figcaption>{selectedDetail.latest_evidence.caption}</figcaption></figure> : <div className="site-empty"><strong>Evidence incomplete</strong><span>No field-evidence image or verified GPS record is available for this pilot site.</span></div>}<div className="evidence-timeline"><p className="eyebrow">EVIDENCE TIMELINE</p>{selectedDetail.timeline.map(([title, detail, state]) => <div className={`timeline-item timeline-item--${state}`} key={title}><i aria-hidden="true" /><div><strong>{title}</strong><span>{detail}</span></div></div>)}</div><small className="site-source">Curated pilot/demo data · {siteDetails.source}</small></> : null}</div>
        <div className="risk-panel"><p className="eyebrow">RESIDUAL RISK & NEXT ACTION</p><div className="risk-selector">{layers?.riskZones.features.map((feature) => <button className={selectedRisk?.id === feature.properties.id ? "active" : ""} key={feature.properties.id} onClick={() => setSelectedRisk(feature.properties)}>{feature.properties.name}</button>)}</div><h3>{selectedRisk?.name ?? "Select a coloured risk zone"}</h3>{selectedRisk ? <><dl><div><dt>Slope</dt><dd>{selectedRisk.conditions.slope_deg}°</dd></div><div><dt>Runoff proxy</dt><dd>{selectedRisk.conditions.runoff_proxy}</dd></div><div><dt>Vegetation</dt><dd>{selectedRisk.conditions.vegetation_condition}</dd></div><div><dt>Terrain / soil</dt><dd>{selectedRisk.conditions.terrain_soil_proxy}</dd></div><div><dt>Drainage distance</dt><dd>{selectedRisk.conditions.distance_to_drainage_m} m</dd></div></dl>{recommendation ? <div className="recommendations"><strong>Recommended Next Action</strong><h4>{recommendation.recommended_next_action.intervention} · {recommendation.recommended_next_action.score}/100</h4>{recommendation.recommended_next_action.reasons.map((reason) => <p key={reason}>{reason}</p>)}{recommendation.recommendations.map((item) => <div className="recommendation-score" key={item.intervention}><span>{item.intervention}</span><b>{item.score}/100</b></div>)}<small>{recommendation.disclaimer}</small></div> : <p>Loading recommendation…</p>}</> : <p>Red shows high runoff risk, amber moderate risk, and green low residual risk.</p>}</div>
        <div className="legend" aria-label="Map legend"><p className="eyebrow">LEGEND</p><p><i className="legend-dot intervention" />Verified intervention</p><p><i className="legend-dot pond" />Farm pond</p><p><i className="legend-swatch high" />High Runoff Risk</p><p><i className="legend-swatch medium" />Moderate risk</p><p><i className="legend-swatch low" />Low risk</p><p><i className="legend-line" />Watershed boundary</p></div>
      </aside></div>
  </section>;
}
