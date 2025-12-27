const BASE_URL = "http://localhost:8000/api";

export async function apiGet(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  return res.json();
}

export async function apiPost(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}
