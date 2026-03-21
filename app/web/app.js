const pretty = (obj) => JSON.stringify(obj, null, 2);

function appendLocalRecord(key, value) {
  const current = JSON.parse(localStorage.getItem(key) || "[]");
  current.push(Object.assign({}, value, { saved_at: new Date().toISOString() }));
  localStorage.setItem(key, JSON.stringify(current));
}

async function jsonFetch(url, options = {}) {
  const res = await fetch(url, options);
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(payload.detail || `HTTP ${res.status}`);
  }
  return payload;
}

const setOutput = (id, data) => (document.getElementById(id).textContent = typeof data === "string" ? data : pretty(data));

document.getElementById("register-user-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  try {
    const data = await jsonFetch("/register_user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: fd.get("name") }),
    });
    appendLocalRecord("registered_users", data);
    setOutput("register-user-output", data);
  } catch (err) {
    setOutput("register-user-output", err.message);
  }
});

document.getElementById("register-property-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  const body = new FormData();
  body.set("property_id", fd.get("propertyId"));
  body.set("owner_public_key", fd.get("ownerPublicKey"));
  body.set("location", fd.get("location"));
  body.set("description", fd.get("description"));
  body.set("media", fd.get("media"));

  try {
    const data = await jsonFetch("/register_property", {
      method: "POST",
      headers: { "x-admin-token": fd.get("adminToken") },
      body,
    });
    appendLocalRecord("registered_properties", Object.assign({}, data, {
      property_id: fd.get("propertyId"),
      owner_public_key: fd.get("ownerPublicKey"),
      location: fd.get("location"),
      description: fd.get("description"),
    }));
    setOutput("register-property-output", data);
  } catch (err) {
    setOutput("register-property-output", err.message);
  }
});

document.getElementById("transfer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);

  const propertyId = fd.get("propertyId").toString();
  const fromPublicKey = fd.get("fromPublicKey").toString().trim();
  const privateKey = fd.get("privateKey").toString().trim();
  const toPublicKey = fd.get("toPublicKey").toString().trim();
  const documentText = fd.get("documentText").toString();
  const mediaHash = fd.get("mediaHash").toString();

  try {
    const txTimestamp = new Date().toISOString();

    const signed = await jsonFetch("/sign_transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        property_id: propertyId,
        from_public_key: fromPublicKey,
        to_public_key: toPublicKey,
        document_text: documentText,
        media_hash: mediaHash,
        tx_timestamp: txTimestamp,
        private_key: privateKey,
      }),
    });

    const signatureB64 = signed.signature;

    const data = await jsonFetch("/transfer_property", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        property_id: propertyId,
        to_public_key: toPublicKey,
        document_text: documentText,
        tx_timestamp: txTimestamp,
        signature: signatureB64,
      }),
    });
    setOutput("transfer-output", { txTimestamp, payloadHash: signed.payload_hash, signatureB64, result: data });
  } catch (err) {
    setOutput("transfer-output", err.message);
  }
});

document.getElementById("property-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = new FormData(e.currentTarget).get("propertyId");
  try {
    setOutput("property-output", await jsonFetch(`/property/${id}`));
  } catch (err) {
    setOutput("property-output", err.message);
  }
});

document.getElementById("history-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = new FormData(e.currentTarget).get("propertyId");
  try {
    setOutput("history-output", await jsonFetch(`/property/${id}/history`));
  } catch (err) {
    setOutput("history-output", err.message);
  }
});

document.getElementById("blockchain-btn").addEventListener("click", async () => {
  try {
    setOutput("blockchain-output", await jsonFetch("/blockchain"));
  } catch (err) {
    setOutput("blockchain-output", err.message);
  }
});
