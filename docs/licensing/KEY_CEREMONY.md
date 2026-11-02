# Key Ceremony & Recovery — Owner Procedure

## 1. Initial key generation (once, offline, owner machine)
1. Obtain the owner-only License Generator (separate EXE; never distributed to customers).
2. On a trusted, preferably offline Windows machine, run it and choose
   "নতুন কী তৈরি করুন" (create new key).
3. Set a strong admin passphrase (≥ 12 chars). The generator creates an Ed25519
   keypair; the private key is encrypted (argon2id → AES-256-GCM) and stored in the
   generator's private data directory. The public key is exported as `public_key.pem`.
4. **Back up the encrypted private key + remember the passphrase** (offline copy on
   encrypted USB, second copy in a safe). Losing both = cannot issue new licenses
   without a key rotation (below).
5. Commit ONLY `public_key.pem` to `src/vybora/licensing/public_key.pem` (public
   material is safe). Never commit the private key or passphrase.
6. Build release → app now verifies licenses signed by this key.

## 2. Issuing a license
Customer sends `.vbr` activation request → generator imports it → owner enters
business name + business id → sign → export `.vbl` → send to customer → customer
imports in app → activated permanently (offline).

## 3. Reissue / machine transfer
Customer's hardware changed → new `.vbr` → generator "reissue/transfer" referencing
old license_id → new `.vbl` with `transfer_of` set → customer imports. Old license is
marked transferred in generator history (administrative record; no online revocation).

## 4. Key rotation (compromise or loss)
1. Generate a NEW keypair (ceremony above).
2. Ship an app update embedding the new public key.
3. Reissue licenses to all customers with the new key.
4. Old licenses fail verification after the update (fail-closed). Communicate clearly
   to customers; provide reissue support.

## 5. What never to do
- Never put the private key/passphrase in Git, CI, email, chat, installers or releases.
- Never run the generator on a customer machine.
- Never share the generator EXE with customers.
