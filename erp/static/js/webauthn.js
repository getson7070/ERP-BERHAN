async function setupWebAuthnLogin() {
  const btn = document.getElementById('webauthn-login');
  if (!btn || !window.PublicKeyCredential) {
    return;
  }
  btn.addEventListener('click', async () => {
    const beginResp = await fetch('/auth/webauthn/login');
    const options = await beginResp.json();
    options.challenge = Uint8Array.from(atob(options.challenge.replace(/_/g, '/').replace(/-/g, '+')), c => c.charCodeAt(0));
    if (options.allowCredentials) {
      options.allowCredentials = options.allowCredentials.map(cred => ({
        ...cred,
        id: Uint8Array.from(atob(cred.id.replace(/_/g, '/').replace(/-/g, '+')), c => c.charCodeAt(0))
      }));
    }
    const cred = await navigator.credentials.get({ publicKey: options });
    const verifyResp = await fetch('/auth/webauthn/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cred)
    });
    if (verifyResp.ok) {
      const data = await verifyResp.json();
      localStorage.setItem('token', data.token);
      window.location = '/';
    }
  });
}

document.addEventListener('DOMContentLoaded', setupWebAuthnLogin);
