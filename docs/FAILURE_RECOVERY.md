# Failure recovery

API down:
- continue local experiments;
- bounded backoff;
- preserve cached data;
- snapshot after recovery.

SDK changed:
- inspect release;
- update deliberately;
- rerun contract/scorer tests;
- do not silently bump during live round.

Bad submission:
- preserve response/lane/ID hash;
- diagnose before retry;
- account for quota.

Dashboard down:
- ignore and use CLI.

LLM down:
- deterministic scheduler continues.

OOM/crash:
- mark run FAILED;
- preserve log/config;
- reduce budget/concurrency;
- continue queue.

Late code regression:
- return to pre-event tag;
- keep run data outside destructive reset;
- rerun doctor.

Network lost:
- hotspot;
- reuse prediction artefact if split fingerprint unchanged.

Time nearly over:
- `qseh emergency`;
- no new research.
