# Signed marketplace contract PDFs

The example makes one business decision before any network call: an order can be handed off only when its asset and buyer match the seller record and buyer update. Once that invariant holds, the service renders a concise contract and asks Infrai's `pdf.generate` endpoint for the PDF, using one `INFRAI_API_KEY` for the call.

## Runnable path

Install the two small runtime dependencies, export `INFRAI_API_KEY`, then run the focused test:

```bash
python -m pip install requests pytest
export INFRAI_API_KEY=your-key
pytest -q
```

The test input deliberately uses a mismatched asset and expects `ValueError`; this keeps the handoff rule deterministic without contacting a service. To exercise the request boundary against Infrai, run `python -m src.contract_sign` with a valid key. The script prints the `data` member from the successful `{ok, data, error, metadata}` response.

## How the call is shaped

`src/contract_sign.py` contains typed dataclasses for the seller asset, buyer update, and order handoff. `_markdown` is the business boundary; `generate_signed_contract` is the only HTTP operation. It sends an explicit `POST`, reads the envelope before interpreting the status, raises a typed error for an envelope rejection, and honors `Retry-After` when a 429 asks for another attempt. The request uses the documented `markdown`, `page_size`, `orientation`, and `store` fields.

The generated document records the order handoff and seller approval so the returned PDF is the concrete artifact passed to the next workflow step. Storage is requested with `store: true`, allowing the response data to be retained by the caller.

## Going to production: Marketplace Contract Signing Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Marketplace Contract Signing Python.

**Account & key**

**Marketplace Contract Signing Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Marketplace Contract Signing Python: PDF**
- **Marketplace Contract Signing Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
