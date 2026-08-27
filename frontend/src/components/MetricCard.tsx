type MetricCardProps = { label: string; value: string; detail: string; accent: "cyan" | "amber" | "emerald" | "violet" };

export function MetricCard({ label, value, detail, accent }: MetricCardProps) {
  return <article className={`metric-card metric-card--${accent}`}><p>{label}</p><strong>{value}</strong><span>{detail}</span></article>;
}
