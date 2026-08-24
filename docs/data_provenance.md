# Data provenance and missingness audit

## UCI Daily Demand Forecasting Orders data

Local file: `data/external/Daily_Demand_Forecasting_Orders.csv`  
SHA-256: `adf8dda021beae76b13b1cbb5b3c075d064f03b3353a711c1ddc357c6f89e924`

The analysed file has 60 rows, 13 columns and zero missing cells. The source schema describes 12 predictors and one total-order target from a Brazilian logistics company. The official record is:

- Ferreira, R. P., Martiniano, A., Ferreira, A., Sassi, R. J., & Silva, R. (2016). *Daily Demand Forecasting Orders* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BC8T

## Chain-of-custody limit

The exact public-mirror URL used to obtain the local bytes was not preserved. Before analysis, the file's dimensions, column names, missingness and target range were checked against the UCI schema, and the bytes were frozen under the hash above. This supports reproducibility from the included bytes but leaves the original download hop unresolved. A future release should fetch directly from the DOI-backed repository and record the response headers and hash.

## Observed versus reconstructed fields

Observed:

- daily target demand in the included dataset;
- calendar and source predictor columns;
- row order and missingness.

Reconstructed for illustration:

- old and updated forecast vintages;
- forecast-revision scores;
- setup and holding costs;
- rolling commitment policies and counterfactual structural regret.

The reconstructed vintages use a causal pooled direct ridge model with target lags, rolling target means and known target-date calendar indicators. It does not use source predictors unavailable at the forecast origin. Costs are stylised at setup values of £60, £120 and £240 and daily holding values of £0.06, £0.12 and £0.24 per order unit.

## Split and missingness

Thirty-one overlapping eight-day windows are reconstructed. Eight windows estimate the score scale, 11 calibrate the split-conformal threshold and 12 form the retrospective evaluation set. The split was fixed in the analysis script. No source-data cells are missing. The design does not reconstruct genuine historical forecasts, supplier constraints or realised service outcomes; those remain structurally missing.
