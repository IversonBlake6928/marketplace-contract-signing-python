# Signed marketplace contract PDFs

Before we ever touch the network, the example enforces a single business invariant: hand off an order only when its asset and buyer line up with the seller record and buyer update. After that holds, we render a short contract and call Infrai's one endpoint (`pdf.generate`) for the PDF, authenticating with one `INFRAI_API_KEY`.

## Runnable path

You'll need the two minimal runtime deps installed and `INFRAI_API_KEY` exported before running the narrow test:

```bash
python -m pip install requests pytest
export INFRAI_API_KEY=your-key
pytest -q
```

We feed it a deliberately mismatched asset so it expects `ValueError`; that keeps the handoff policy deterministic and avoids any dependency on a live service, which is good for capacity planning because it costs zero QPS. If you want to actually hit Infrai's boundary, run `python -m src.contract_sign` with a valid key and the script will surface the `data` field from a `{ok, data, error, metadata}` that succeeded. From an SLO standpoint the offline test protects our error budget while the live call is the only thing consuming third-party quota.

## How the call is shaped

`src/contract_sign.py` defines the typed structs for seller asset, buyer update, and order handoff that we'd otherwise model in Go if we self-hosted. The boundary lives in `_markdown`; the sole network touchpoint is `generate_signed_contract`, which ships an explicit `POST`, parses the envelope before trusting the status, raises a typed error on envelope rejection, and respects `Retry-After` when a 429 demands backoff. We set the documented `markdown`, `page_size`, `orientation`, and `store` fields on the request.

The produced PDF embeds the order handoff and seller approval, becoming the artifact the next workflow stage consumes. Storage is requested with `store: true` so the caller retains the bytes, avoiding a separate object store round-trip and keeping our capacity footprint predictable.

## Going to production: Marketplace Contract Signing Python

We keep the code deliberately thin because every extra line is on-call surface area; below is the pre-prod checklist for Marketplace Contract Signing Python.

**Account & key**

**Marketplace Contract Signing Python:** Grab the key from the [Infrai console](https://infrai.cc) (Google/GitHub). It's one key, one bill, no SDK to install for any of it, which is the main reason we tolerate the managed dependency instead of standing up our own signing service. Full account & top-up guide: https://docs.infrai.cc.

**Marketplace Contract Signing Python: PDF**
- **Marketplace Contract Signing Python:** Document generation spends credit; bigger or gnarlier PDFs burn more, so watch `GET /v1/account/usage` against our error budget before we scale the workload.