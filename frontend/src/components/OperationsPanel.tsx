import { useState } from "react";

type Role = "Field Worker" | "Supervisor" | "Auditor" | "Admin";
const views: Record<Role, { title: string; actions: string[]; note: string }> = {
  "Field Worker": { title: "Field work", actions: ["Create or update intervention", "Save field draft locally", "Upload evidence and submit for review"], note: "GPS, capture time, file checks, and sync status are captured before review." },
  Supervisor: { title: "Review assignment", actions: ["Inspect submitted interventions", "Review evidence and GeoProof factors", "Verify or return for clarification"], note: "Low-confidence or inconsistent evidence remains in Needs Review." },
  Auditor: { title: "Audit trail", actions: ["Inspect evidence history", "Read score-factor explanations", "Approve or reject with comments"], note: "Verification is decision support, not a fraud-proof claim." },
  Admin: { title: "Programme administration", actions: ["Manage organisations and users", "Maintain watersheds and intervention types", "Inspect risk-zone and operations records"], note: "Administrative changes are recorded in the audit history." },
};

export function OperationsPanel() {
  const [role, setRole] = useState<Role>("Field Worker");
  const view = views[role];
  return <section className="section-note operations-panel" aria-label="Production operations workflow">
    <div className="operations-header"><div><p className="eyebrow">PILOT WORKFLOW</p><strong>{view.title}</strong></div><select value={role} onChange={(event) => setRole(event.target.value as Role)} aria-label="Preview role workflow">{Object.keys(views).map((item) => <option key={item}>{item}</option>)}</select></div>
    <ul>{view.actions.map((action) => <li key={action}>{action}</li>)}</ul><span>{view.note}</span>
  </section>;
}
