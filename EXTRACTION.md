# Extraction provenance

Source repository: https://github.com/Huang-Xinghao/paper_agent

Source HEAD: `97c64fb8da87a8fd8e0fb8a5d91821a481a31ed3`

Extracted on 2026-11-19 from the working tree, including uncommitted Wiki changes.
This is a code snapshot; the source repository and its working tree were preserved.

Included: Wiki source preparation, evidence validation, review, recovery, publication,
retrieval, relations, metadata, prompts, PDF and figure helpers, model transport,
atomic storage, batch adapter, visualizer and focused regression tests.

Adaptations: independent package and configuration namespace; standalone curation
loop and CLI; packaged embedding worker; installation metadata and CI.
Tests that require the original coordinator, role session store, Web API or full
paper workflow were excluded. Core Wiki regression tests were retained.

No source `.env`, credentials, research corpus, PDFs, local resource catalog,
runtime artifacts or original Git history were copied.
