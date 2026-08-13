---
title: Backend API
description: Generated from create_app().openapi() for the Research Console.
source: generated
generatedFromSha: 0b0fe69f467df29751a6e316ad852083503d48b6
generatedAt: 2026-08-13T11:38:41+00:00
---

# Backend API

Generated from commit `0b0fe69f467df29751a6e316ad852083503d48b6`.

OpenAPI `3.1.0` — 33 paths from the live FastAPI application.

Swagger UI is isolated at `/api/dev/docs` so it does not collide with the SPA `/docs` page.

## `POST /api/actions/autopilot/start`

Start Autopilot

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/autopilot/stop`

Stop Autopilot

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/build-ensemble`

Build Ensemble

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| strategy | query | no | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `POST /api/actions/jobs/{job_id}/stop`

Stop Job

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| job_id | path | yes | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `POST /api/actions/official-baseline`

Official Baseline

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/promote-ensemble`

Promote Ensemble

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/pull-datasets`

Pull Datasets

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/race/start`

Start Race

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| profile | query | no | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `POST /api/actions/refresh-event`

Refresh Event

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/save-ensemble`

Save Ensemble

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| strategy | query | no | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `POST /api/actions/scorer-parity`

Scorer Parity

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/snapshot-event`

Snapshot Event

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `POST /api/actions/submit-live/{candidate_id}`

Submit Live

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| candidate_id | path | yes | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `POST /api/actions/submit-practice/{candidate_id}`

Submit Practice

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| candidate_id | path | yes | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `POST /api/actions/validate/{candidate_id}`

Validate Submission

### Parameters

| Name | In | Required | Type | Meaning |
| --- | --- | --- | --- | --- |
| candidate_id | path | yes | string |  |

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |
| 422 | Validation Error | HTTPValidationError ({detail: array[ValidationError]}) |

## `GET /api/compute`

Get Compute

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/data-lab`

Get Data Lab

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/docs`

Get Documentation

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/ensembles`

Get Ensembles

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/event-control`

Get Event Control

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/event-status`

Get Event Status

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/events`

Events

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/experiments`

Get Experiments

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/feature-lab`

Get Feature Lab

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/health`

Health

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/leaderboard`

Get Leaderboard

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/models`

Get Models

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/overview`

Get Overview

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/repository`

Get Repository

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/round-room`

Get Round Room

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/staking`

Get Staking

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/submission`

Get Submission

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

## `GET /api/validation`

Get Validation

### Responses

| Status | Description | Schema |
| --- | --- | --- |
| 200 | Successful Response |  |

