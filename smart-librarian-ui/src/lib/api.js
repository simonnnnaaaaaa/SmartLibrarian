export const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health failed: ${res.status} ${res.statusText}`);
  return res.json();
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try { detail = await res.text(); } catch {}
    const err = new Error(`${url} → ${res.status} ${res.statusText} ${detail}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function recommend(question) {
  return postJSON(`${API_BASE}/api/recommend`, { question });
}

export async function generateImage(title, hint = "", style = "cinematic cover") {
  const res = await fetch(`${API_BASE}/api/image`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, hint, style })
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`/api/image → ${res.status} ${res.statusText} ${text}`);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
