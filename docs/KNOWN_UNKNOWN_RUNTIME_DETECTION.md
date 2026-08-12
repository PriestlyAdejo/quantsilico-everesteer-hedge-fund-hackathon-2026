# Known / unknown / runtime detection

| Topic | Current status | Confidence | Runtime detector |
|---|---|---:|---|
| SDK package `everestapi` | confirmed | very high | package metadata |
| observed version 0.3.22 on Aug 11 | confirmed at research time | very high | PyPI + installed version |
| futures/Himalayas | invitation + docs | high | event/universe |
| target `target_everest_20` | current docs | high | schema/scoring metadata |
| validation = practice lane | current docs | high | `get_started`, split IDs |
| live = open round | current docs + invite | high | `get_started` |
| score blend CORR/AIMC/NCORR | current docs | high | `explain_scoring` |
| exact weights | unknown | runtime | `explain_scoring` |
| number/duration rounds | unknown | runtime | event state/Discord |
| account-wide upload cap value | unknown | runtime | API response/state |
| event stake mechanics | unknown | runtime | event UI + `get_event_staking` |
| virtual vs real-money stake | unknown | runtime | explicit mechanism classification |
| server compute access | unknown | runtime | capability probe |
| rows/features/expeds | unknown | runtime | dataset info/audit |
| auxiliary targets | unknown | runtime | schema |
| held-out final | must not assume | runtime | `get_started`/leaderboard availability |
| previous winner method | not recovered | low | primary winner post/Discord |

## Event snapshot record

Write immutable snapshots under ignored `runs/event/`:

```json
{
  "snapshot_id": "",
  "observed_at": "",
  "sdk_version": "",
  "api_scope": "",
  "key_fingerprint": "",
  "event_id": "",
  "tournament": "",
  "started": {},
  "dataset_info": {},
  "scoring": {},
  "staking": {},
  "submission_cap": null,
  "server_compute": {}
}
```

Every external submission references the snapshot in force at submission time.
