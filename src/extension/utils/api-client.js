export async function submitJob(payload) {
  const response = await fetch("http://127.0.0.1:8765/jobs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return response.json();
}

