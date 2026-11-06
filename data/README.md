# Data dictionary and provenance

Private passenger auto liability/medical data accessed from the CAS research resource, compiled for the CAS by S&P Global Market Intelligence. Net of reinsurance; source Schedule P monetary units are USD thousands. Accident years 1998–2007 and lags one through ten. Fixed codes 43, 388, 1090, 2003 and 4839 form an illustrative panel, not a representative market sample.

| Field | Meaning |
| --- | --- |
| GRCODE, GRNAME | Insurer/group identifier and source name |
| AccidentYear | Year generating the insured loss |
| DevelopmentYear | Calendar valuation year of the cell |
| DevelopmentLag | Annual development age, starting at 1 |
| CumPaidLoss | Cumulative net paid losses and allocated expenses |
| IncurredLosses | Source reported incurred losses, retained but not used as paid outcomes |
| EarnedPremNet | Net earned premium exposure base |
| BulkLoss | Source bulk/IBNR amount; not the fitted model target |
| PostedReserves2007 | Source posted reserves; not used as a future-outcome substitute |

Amounts retain published Schedule P USD-thousands units. The analytical methods fit paid
triangles, not incremental loss rows. Lags 1–10 are finite observed development. Data are
net of reinsurance and insurer groups can have internal reinsurance relationships. Do not
sum this illustrative panel into a market estimate.
