export type Watershed = { id: string; name: string; data_status: string; provenance: Record<string, string> };

const API_BASE = "http://localhost:8000/api/v1";

export async function getWatersheds(): Promise<Watershed[]> {
  const response = await fetch(`${API_BASE}/watersheds`);
  if (!response.ok) throw new Error("Could not load watershed data.");
  return response.json() as Promise<Watershed[]>;
}
