const SESSION_ID = 'sess_' + Math.random().toString(36).substr(2, 9);
const themeBtn = document.getElementById("themeToggle");

themeBtn.addEventListener("click", () => {
    document.body.classList.toggle("light");

    if (document.body.classList.contains("light")) {
        themeBtn.innerText = "☀ Light Mode";
        localStorage.setItem("theme", "light");
    } else {
        themeBtn.innerText = "🌙 Dark Mode";
        localStorage.setItem("theme", "dark");
    }
});

// Load saved theme configuration
window.addEventListener("load", () => {
    const saved = localStorage.getItem("theme");
    if (saved === "light") {
        document.body.classList.add("light");
        themeBtn.innerText = "☀ Light Mode";
    }
});

let isBusy = false;

const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// Handle Splash Screen fade-out and initial automatic Greeting
window.addEventListener("load", () => {
    setTimeout(() => {
        const splash = document.getElementById("splashScreen");
        if (splash) splash.style.display = "none";
    }, 5000);

    setTimeout(() => {
        sendToBot("hello");
    }, 5500);
});

inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !isBusy) sendMessage();
});

function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isBusy) return;
    inputEl.value = '';
    appendMessage(text, 'user');
    sendToBot(text);
}

function restartChat() {
    messagesEl.innerHTML = '';
    sendToBot("restart");
}

function appendMessage(text, sender, severity, type) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message ' + sender;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = sender === 'bot' ? '🤖' : '🧑';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (severity) bubble.classList.add('severity-' + severity);
    if (type === 'emergency') bubble.classList.add('emergency');

    bubble.innerHTML = formatText(text);

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollDown();
}

function formatText(text) {
    text = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    text = text.replace(/━+/g, '<hr style="border:none;border-top:1px solid #30363d;margin:8px 0">');
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#58a6ff">$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function showTyping() {
    const w = document.createElement('div');
    w.className = 'typing-wrapper';
    w.id = 'typing';

    const av = document.createElement('div');
    av.className = 'msg-avatar';
    av.textContent = '🤖';

    const dots = document.createElement('div');
    dots.className = 'typing-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';

    w.appendChild(av);
    w.appendChild(dots);
    messagesEl.appendChild(w);
    scrollDown();
}

function removeTyping() {
    const t = document.getElementById('typing');
    if (t) t.remove();
}

function scrollDown() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setBusy(val) {
    isBusy = val;
    inputEl.disabled = val;
    sendBtn.disabled = val;
    sendBtn.style.opacity = val ? '0.5' : '1';
}

async function sendToBot(message) {
    setBusy(true);
    showTyping();

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: SESSION_ID })
        });

        if (!res.ok) throw new Error('Server returned ' + res.status);

        const data = await res.json();
        removeTyping();
        appendMessage(data.message, 'bot', data.severity || null, data.type || null);

    } catch (err) {
        removeTyping();
        appendMessage('Connection error. Please make sure the server is running and refresh the page.', 'bot');
        console.error(err);
    }
    setBusy(false);
}

// Download PDF function structured securely outside sendToBot function boundary
function downloadPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    let text = "MediBot Patient Report\n\n";
    const messages = document.querySelectorAll(".message");

    messages.forEach((msg) => {
        const isUser = msg.classList.contains("user");
        const role = isUser ? "User: " : "Bot: ";
        text += role + msg.innerText + "\n\n";
    });

    doc.text(text, 10, 10);
    doc.save("patient-report.pdf");
}