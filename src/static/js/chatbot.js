/*
 * Chatbot widget behaviour.
 * Owner: H.G.P.C. Sagara (PM & Integration Dev)
 *
 * The whole conversation lives in this browser tab (the `history` array);
 * each request sends the message plus recent history, and the server stays
 * stateless. Replies are inserted as plain text — never as HTML — so a
 * model reply can never inject markup or scripts into the page.
 */
(function () {
  "use strict";

  const toggle = document.getElementById("chatbot-toggle");
  const panel = document.getElementById("chatbot-panel");
  const closeBtn = document.getElementById("chatbot-close");
  const messagesBox = document.getElementById("chatbot-messages");
  const form = document.getElementById("chatbot-form");
  const input = document.getElementById("chatbot-input");
  if (!toggle || !panel) return;

  const history = [];

  function addMessage(role, text) {
    const div = document.createElement("div");
    div.className =
      "chatbot-msg " + (role === "user" ? "chatbot-msg-user" : "chatbot-msg-bot");
    // Minimal markdown: only **bold** is rendered, via safe DOM nodes.
    text.split(/\*\*(.+?)\*\*/g).forEach(function (part, i) {
      if (i % 2 === 1) {
        const b = document.createElement("strong");
        b.textContent = part;
        div.appendChild(b);
      } else {
        div.appendChild(document.createTextNode(part));
      }
    });
    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return div;
  }

  toggle.addEventListener("click", function () {
    panel.classList.toggle("d-none");
    if (!panel.classList.contains("d-none")) input.focus();
  });
  closeBtn.addEventListener("click", function () {
    panel.classList.add("d-none");
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    input.disabled = true;
    addMessage("user", message);
    const thinking = addMessage("bot", "…");

    try {
      const response = await fetch("/chatbot/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, history: history }),
      });
      const data = await response.json();
      const reply = data.reply || data.error || "Sorry, something went wrong.";
      thinking.remove();
      addMessage("bot", reply);
      history.push({ role: "user", content: message });
      history.push({ role: "assistant", content: reply });
      if (history.length > 20) history.splice(0, history.length - 20);
    } catch (err) {
      thinking.remove();
      addMessage("bot", "Network error — please check the connection and try again.");
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
})();
