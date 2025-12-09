# Security Policy

## Reporting a vulnerability
Please email **security@google-authz.dev** with details about the vulnerability, proof of concept, and any logs or reproduction steps. Encrypt submissions with our GPG key if possible (fingerprint TBD).

We aim to acknowledge new reports within **3 business days** and provide a mitigation ETA within **10 business days**. Critical issues may trigger out-of-band updates.

## Supported versions
- Security fixes are applied to the latest `main` branch and the most recent tagged release.
- Older releases will receive fixes on a best-effort basis only when they are easy to backport.

## Coordinated disclosure
We prefer coordinated disclosure. Please do not create public issues until a fix is released. Once patched, we will credit reporters (unless anonymity is requested) in the `CHANGELOG` or GitHub Release notes.

## Additional resources
- [`docs/security.md`](docs/security.md) covers secret management, dependency scanning, and rotation guidance.
- [`docs/deployment.md`](docs/deployment.md) explains how to inject secrets securely across environments.
