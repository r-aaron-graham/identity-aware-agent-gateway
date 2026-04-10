let demoTokens = {};

async function loadTokens() {
  const res = await fetch('/api/v1/auth/demo-tokens');
  const data = await res.json();
  demoTokens = data;
  const box = document.getElementById('tokens');
  const roleSelect = document.getElementById('roleSelect');
  roleSelect.innerHTML = '';
  const lines = [];
  Object.entries(data).forEach(([key, value]) => {
    lines.push(`${key} (${value.role})\n${value.token}\n`);
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = `${key} (${value.role})`;
    roleSelect.appendChild(opt);
  });
  box.textContent = lines.join('\n');
  if (roleSelect.options.length > 0) {
    roleSelect.value = 'analyst' in data ? 'analyst' : roleSelect.options[0].value;
    setSelectedToken();
  }
  roleSelect.onchange = setSelectedToken;
}

function setSelectedToken() {
  const role = document.getElementById('roleSelect').value;
  const tok = demoTokens[role] ? demoTokens[role].token : '';
  document.getElementById('token').value = tok;
}

async function loadWhoAmI() {
  const token = document.getElementById('token').value.trim();
  const res = await fetch('/api/v1/whoami', { headers: { Authorization: `Bearer ${token}` } });
  document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
}

async function submitRequest() {
  const token = document.getElementById('token').value.trim();
  const prompt = document.getElementById('prompt').value;
  const requested_tool = document.getElementById('tool').value || null;
  const sensitivity = document.getElementById('sensitivity').value;
  const res = await fetch('/api/v1/agent/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ prompt, requested_tool, sensitivity }),
  });
  document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
}

async function loadReviews() {
  const token = document.getElementById('token').value.trim();
  const res = await fetch('/api/v1/reviews', {
    headers: { Authorization: `Bearer ${token}` },
  });
  document.getElementById('reviews').textContent = JSON.stringify(await res.json(), null, 2);
}

async function loadMetrics() {
  const token = document.getElementById('token').value.trim();
  const res = await fetch('/api/v1/metrics', {
    headers: { Authorization: `Bearer ${token}` },
  });
  document.getElementById('reviews').textContent = JSON.stringify(await res.json(), null, 2);
}

async function resolveReview() {
  const token = document.getElementById('token').value.trim();
  const reviewId = document.getElementById('reviewId').value;
  const resolution = document.getElementById('resolution').value;
  const note = document.getElementById('reviewNote').value;
  const res = await fetch(`/api/v1/reviews/${reviewId}/resolve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ resolution, note }),
  });
  document.getElementById('reviews').textContent = JSON.stringify(await res.json(), null, 2);
}
