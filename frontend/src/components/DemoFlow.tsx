const steps = ["Select Watershed", "Upload Field Evidence", "GeoProof Verification", "Satellite Impact", "Risk and Recommendation", "Download Report"];

export function DemoFlow({ loaded }: { loaded: boolean }) {
  return <section className="demo-flow" aria-label="Guided SIH demo flow"><div><p className="eyebrow">GUIDED 3-MINUTE DEMO</p><h2>Tell the evidence story, step by step</h2></div><ol>{steps.map((step, index) => <li className={loaded ? "ready" : ""} key={step}><span>{index + 1}</span>{step}</li>)}</ol></section>;
}
