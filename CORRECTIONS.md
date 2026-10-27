# Corrections

## 2026-10-27 — errata to certified-commitment-horizons 3.0.0-candidate (DOI 10.5281/zenodo.22086554)

The archived PDF, the manuscript source, the Zenodo deposit and the tag `v3.0.0-candidate` are unchanged. These errata were confirmed by the Evidence Press archive audit and are also shown at <https://evidencepress.org/releases/certified-commitment-horizons/>.

1. Corrected an attribution in §14, “Scaling”. The archived text says “the interval binary search never needed more than 16 exact shortest-path evaluations”. The count of 16 covers the whole certified computation: one evaluation at r = 0, the binary search, one refinement and the Newton steps. The sentence should read “The certified computation never needed more than 16 exact shortest-path evaluations in total”, and the Table 6 column “Shortest paths” should be read as the total.

   The count itself is correct. No theorem, certificate, computation or stated result is affected.
