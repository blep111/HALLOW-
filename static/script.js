async function startShare() {
  const cookie = document.getElementById("cookie").value.trim();
  const link = document.getElementById("link").value.trim();
  const limit = document.getElementById("limit").value.trim();
  const responseArea = document.getElementById("response");

  responseArea.innerHTML = "🕷️ Processing your request... Please wait.";

  if (!cookie || !link || !limit) {
    responseArea.innerHTML = "⚠️ Please fill out all fields.";
    return;
  }

  try {
    const res = await fetch("/api/share", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookie, link, limit })
    });

    const data = await res.json();
    if (data.status) {
      responseArea.innerHTML = `<span style="color:lime;">${data.message}</span>`;
    } else {
      responseArea.innerHTML = `<span style="color:red;">${data.message}</span>`;
    }
  } catch (err) {
    responseArea.innerHTML = "👻 Something went wrong. Please try again later.";
    console.error(err);
  }
}