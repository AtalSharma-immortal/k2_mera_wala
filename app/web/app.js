import { sign, getPublicKey } from "https://cdn.jsdelivr.net/npm/@noble/secp256k1@2.2.3/+esm";

const pretty = (obj) => JSON.stringify(obj, null, 2);
const toHex = (bytes) => Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
const hexToBytes = (hex) => new Uint8Array(hex.match(/.{1,2}/g).map((b) => parseInt(b, 16)));

async function sha256Hex(input) {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return toHex(new Uint8Array(digest));
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

function canonicalPayloadHash({ propertyId, fromPublicKey, toPublicKey, documentHash, mediaHash, timestamp }) {
  const canonical = JSON.stringify({
    document_hash: documentHash,
    from_public_key: fromPublicKey,
    media_hash: mediaHash,
    property_id: propertyId,
    timestamp,
    to_public_key: toPublicKey,
  });
  return sha256Hex(canonical);
}

document.getElementById("register-user-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  try {
    const data = await jsonFetch("/register_user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: fd.get("name") }),
    });
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
    const derivedPub = toHex(getPublicKey(privateKey, false).slice(1));
    if (derivedPub !== fromPublicKey) {
      throw new Error("Private key does not match the provided owner public key");
    }

    const documentHash = await sha256Hex(documentText);
    const txTimestamp = new Date().toISOString();
    const payloadHash = await canonicalPayloadHash({
      propertyId,
      fromPublicKey,
      toPublicKey,
      documentHash,
      mediaHash,
      timestamp: txTimestamp,
    });

    const sigHex = await sign(payloadHash, privateKey, { der: false });
    const signatureB64 = btoa(String.fromCharCode(...hexToBytes(sigHex)));

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
    setOutput("transfer-output", { txTimestamp, payloadHash, signatureB64, result: data });
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
