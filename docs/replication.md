# Replication across seeds

The same question run on 20 independent seeds (1 to 20), 480 paths each over 60 months, version 1.2.0. Each seed is an independent family of random streams, so the seeds are independent replications of a run of exactly this size (no adaptive sampling). Produced by `python tools/replicate.py --seeds 20 --paths 480`; the per seed figures are in `replication.json`.

Question: Which AI regulatory instrument best reduces expected harm from frontier AI over the next five years, keeping the technology sector's net loss below $400bn and the gross social cost under $150bn?

## The decision

Under the expected value rule: Liability with a safe harbour in 20 of 20 seeds.

Under the conservative rule (within the constraints in at least 90% of resamples): Liability with a safe harbour in 13 of 20, Transparency and disclosure in 7 of 20.

| Alternative | Preferred (share of seeds) | Preferred, conservative rule | Within the constraints (share of seeds) | Mean share of resamples within |
|---|---:|---:|---:|---:|
| Status quo (voluntary commitments) | 0% | 0% | 100% | 1.00 |
| Transparency and disclosure | 0% | 35% | 100% | 1.00 |
| Compute threshold reporting | 0% | 0% | 100% | 1.00 |
| Mandatory third party evaluation | 0% | 0% | 100% | 1.00 |
| Risk tiering (EU style) | 0% | 0% | 75% | 0.69 |
| Frontier licensing | 0% | 0% | 0% | 0.00 |
| Strict liability | 0% | 0% | 0% | 0.00 |
| Liability with a safe harbour | 100% | 65% | 100% | 0.90 |
| Six month moratorium above the threshold | 0% | 0% | 100% | 1.00 |

## The estimates and their intervals

Two checks on what a single run reports. The spread of an estimate across seeds (its standard deviation) should equal the standard error a run reports: a ratio near one. And a run's 95% interval should contain the truth 95% of the time; the truth is not known, so the mean of the other 19 seeds stands in for it, and because that mean is itself an estimate a perfectly calibrated interval would contain it about 94% of the time.

**Net social value ($bn)**

| Alternative | Pooled mean | SD across seeds | Mean reported SE | Ratio | Interval contains the mean of the other seeds |
|---|---:|---:|---:|---:|---:|
| Transparency and disclosure | 27.56 | 1.06 | 1.14 | 0.93 | 19 of 20 |
| Compute threshold reporting | 11.40 | 1.05 | 0.96 | 1.09 | 17 of 20 |
| Mandatory third party evaluation | 21.32 | 2.09 | 2.19 | 0.95 | 19 of 20 |
| Risk tiering (EU style) | -69.27 | 1.32 | 1.44 | 0.92 | 19 of 20 |
| Frontier licensing | -104.66 | 1.40 | 1.52 | 0.93 | 19 of 20 |
| Strict liability | -4.72 | 1.41 | 1.07 | 1.32 | 15 of 20 |
| Liability with a safe harbour | 37.20 | 2.31 | 2.27 | 1.02 | 17 of 20 |
| Six month moratorium above the threshold | -114.52 | 1.25 | 1.60 | 0.78 | 20 of 20 |

Overall: 145 of 160 intervals (91%) contain the mean of the other seeds, against about 94% for a perfectly calibrated interval.

**Industry value change ($bn)**

| Alternative | Pooled mean | SD across seeds | Mean reported SE | Ratio | Interval contains the mean of the other seeds |
|---|---:|---:|---:|---:|---:|
| Transparency and disclosure | 46.73 | 3.97 | 4.18 | 0.95 | 18 of 20 |
| Compute threshold reporting | 168.78 | 4.63 | 4.12 | 1.12 | 17 of 20 |
| Mandatory third party evaluation | -58.13 | 6.25 | 6.99 | 0.89 | 19 of 20 |
| Risk tiering (EU style) | -396.25 | 5.38 | 5.51 | 0.98 | 18 of 20 |
| Frontier licensing | -493.71 | 7.50 | 6.85 | 1.10 | 18 of 20 |
| Strict liability | -1,249.65 | 6.69 | 8.81 | 0.76 | 20 of 20 |
| Liability with a safe harbour | -387.41 | 5.76 | 8.18 | 0.70 | 20 of 20 |
| Six month moratorium above the threshold | -7.05 | 4.98 | 5.09 | 0.98 | 18 of 20 |

Overall: 148 of 160 intervals (92%) contain the mean of the other seeds, against about 94% for a perfectly calibrated interval.

**Probability of a catastrophe**

| Alternative | Pooled mean | SD across seeds | Mean reported SE | Ratio | Interval contains the mean of the other seeds |
|---|---:|---:|---:|---:|---:|
| Status quo (voluntary commitments) | 15.16% | 0.14% | 0.16% | 0.89 | 19 of 20 |
| Transparency and disclosure | 15.16% | 0.14% | 0.16% | 0.89 | 19 of 20 |
| Compute threshold reporting | 14.67% | 0.14% | 0.15% | 0.91 | 19 of 20 |
| Mandatory third party evaluation | 12.90% | 0.08% | 0.12% | 0.65 | 20 of 20 |
| Risk tiering (EU style) | 14.66% | 0.14% | 0.15% | 0.91 | 20 of 20 |
| Frontier licensing | 14.55% | 0.13% | 0.15% | 0.87 | 20 of 20 |
| Strict liability | 14.56% | 0.13% | 0.15% | 0.85 | 19 of 20 |
| Liability with a safe harbour | 12.30% | 0.09% | 0.11% | 0.75 | 20 of 20 |
| Six month moratorium above the threshold | 14.20% | 0.14% | 0.14% | 1.00 | 19 of 20 |

Overall: 175 of 180 intervals (97%) contain the mean of the other seeds, against about 94% for a perfectly calibrated interval.

The intervals of one alternative across seeds are independent; those of different alternatives within a seed are not (they share the seed's random numbers), so the overall shares are descriptive and carry no test.
