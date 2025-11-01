async function startShare() {
  const cookie = document.getElementById('cookie').value.trim();
  const link = document.getElementById('link').value.trim();
  const limit = document.getElementById('limit').value.trim();
  const responseDiv = document.getElementById('response');

  if (!cookie || !link || !limit) {
    responseDiv.innerHTML = "⚠️ Missing input — please complete all fields!";
    return;
  }

  responseDiv.innerHTML = "💻 Processing spell... connecting to spirits...";

  try {
    const res = await fetch("/api/share", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookie, link, limit })
    });

    const data = await res.json();

    if (data.status) {
      responseDiv.innerHTML = `🟢 ${data.message}`;
    } else {
      responseDiv.innerHTML = `🔴 ${data.message}`;
    }
  } catch (err) {
    responseDiv.innerHTML = "💀 Connection lost... spirits interrupted the process!";
  }
}