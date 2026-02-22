const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
console.log("API BASE =", API)
