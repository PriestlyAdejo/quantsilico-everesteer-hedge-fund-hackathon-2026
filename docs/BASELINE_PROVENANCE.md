# Baseline provenance

The official public futures starter was retrieved on 13 August 2026 from:

`https://raw.githubusercontent.com/everestquant/example-scripts/main/himalayas/futures_starter.py`

Its SHA-256 was:

`e3d35ca62db8e72ae29a0aa8861a92a323cb3854edf6bb1c4d3e94d96d041396`

The `organiser_lgbm` recipe reproduces its estimator parameters, 100-exped
holdout, 20-exped embargo, target filtering, and local `-1 -> NaN` encoding.
Numeric parity is data-dependent and is reported separately.

`reference_lgbm` remains an independently selected, regularised LightGBM reference
used to make local experiments comparable. Its metadata records:

- `organiser_parity_status`: `SOURCE_RETRIEVED`
- source, retrieval date and hash are stored in model metadata;
- numeric parity remains `UNKNOWN` until run on a fingerprinted dataset with
  compatible dependency versions.
