# Evidence index

This index maps manuscript claims to immutable local receipts. Hashes are SHA-256 over the exact
receipt bytes. Development evidence is selection-exposed unless explicitly labeled as unchanged
fresh replication. No listed artifact is a protected finding.

| ID | Scientific role | Exact receipt | SHA-256 |
|---|---|---|---|
| E01 | Hourly process signatures | [`../development-receipts/01_fresh_process_signatures.json`](../development-receipts/01_fresh_process_signatures.json) | `53cb9e82d71ed5d5b16b2adfd1a99512d9a76c48bc28a9a3a42745aa2c2df6cb` |
| E02 | Drift/composition falsifier | [`../development-receipts/02_drift_composition_falsifier.json`](../development-receipts/02_drift_composition_falsifier.json) | `8f8765ad35db116bb30d64f45d3c9325edc5bb46bcd6863972878f3f85c2c699` |
| E03 | Arrival component comparison | [`../development-receipts/03_arrival_model_comparison.json`](../development-receipts/03_arrival_model_comparison.json) | `810dc73970961bc69386041973c349847b151208d8488f959aaa8e69321353b8` |
| E04 | Nonzero sign comparison | [`../development-receipts/04_nonzero_sign_model_comparison.json`](../development-receipts/04_nonzero_sign_model_comparison.json) | `793650747f5d415a2a61ddde30d6b1d1ff5e4782b4c5fb51b7d15ae3cf86fd29` |
| E05 | Nonzero magnitude/residual comparison | [`../development-receipts/05_nonzero_magnitude_model_comparison.json`](../development-receipts/05_nonzero_magnitude_model_comparison.json) | `f5a0aff4ba388852752aaadfa8f3b98badee0a6d55e5c1bc0d78f58ba5f80fe7` |
| E05F | Retained failed magnitude execution | [`../development-receipts/05_nonzero_magnitude_model_comparison.failed-nameerror.json`](../development-receipts/05_nonzero_magnitude_model_comparison.failed-nameerror.json) | `1aaf83367ba4aa70ee7e091b77a3d61400c9c7726d08ab890ecf138729817820` |
| E06F | Retained semantic-inventory timeout | [`../development-receipts/06_development_semantic_inventory.failed-timeout.json`](../development-receipts/06_development_semantic_inventory.failed-timeout.json) | `3cf88100b3df84f5688f1bb9ec09de56f6d032260f959ea79d69bc0acf9f18cf` |
| E08 | Semantic/regime falsifier | [`../development-receipts/08_semantic_composition_falsifier.json`](../development-receipts/08_semantic_composition_falsifier.json) | `578e427fcc71068ccc9a27b509b40244e4f2e1ded35aafe5bc63ddb81b49d487` |
| E09 | Predeclared CLOB measurement manifest | [`../development-receipts/09_fixed_clob_measurement_manifest.json`](../development-receipts/09_fixed_clob_measurement_manifest.json) | `e4270a572f3dd9df26d42e4fb23ce3f4ec66d5e3618dd9e03b1a56b9d882ec18` |
| E10 | Five-minute/source measurement falsifier | [`../development-receipts/10_five_minute_measurement_falsifier.json`](../development-receipts/10_five_minute_measurement_falsifier.json) | `37bc412943cba22665b26f6b2de6f5b9605376d79d510346536bf85834bcedd9` |
| E11 | Whole-event uncertainty and prevalence | [`../development-receipts/11_event_cluster_process_uncertainty.json`](../development-receipts/11_event_cluster_process_uncertainty.json) | `7262b65b8456577c097f64525ef83e57c6ffe37066e0a84559c78c858e2aeda1` |
| E12 | Complete process-family comparison | [`../development-receipts/12_composed_process_family_comparison.json`](../development-receipts/12_composed_process_family_comparison.json) | `2c107a29710e3dd9d13cbf24be00e655b4b0a5c3a628fd8026670a1ad88cd9c5` |
| E14 | Formal arrival rejection | [`../development-receipts/14_formal_hurdle_arrival_freeze.json`](../development-receipts/14_formal_hurdle_arrival_freeze.json) | `2e59fc3be4a6b9157b184cadfcc06eccf946c2131d3f1b12f8fdf44b97f0f7e8` |
| E15 | Boundary, coordinate, maturity, and six-hour-clock robustness | [`../development-receipts/15_representation_robustness.json`](../development-receipts/15_representation_robustness.json) | `757ee06535d3e7e06b8ccc5401aa027266122adaf18b253729ac021cc72bcfc9` |
| E16 | Exact source-03 reproduction and reconstructible all-development arrival hazards | [`../development-receipts/16_freeze_arrival_hazard.json`](../development-receipts/16_freeze_arrival_hazard.json) | `21c3d08cc236953d1ad7e2b6ddc3986db0528d90e9b7813bd31614d97f0f9314` |
| E18 | Governed formal development and independent freeze of the continuous arrival hazard | [`../development-receipts/18_formal_continuous_arrival_hazard.json`](../development-receipts/18_formal_continuous_arrival_hazard.json) | `417e7c9de63538f558a1cdd97609d6d6c82a49b7195bebaee830f8aafec0f192` |
| R01 | Later process-signature replication | [`../successor-corpus/development-receipts/01_fresh_process_signatures.json`](../successor-corpus/development-receipts/01_fresh_process_signatures.json) | `d6d652b20d9458e6472e0d8dddf48aaa6e27946e268bd802580961d9e9972f57` |
| R08 | Later semantic/regime replication | [`../successor-corpus/development-receipts/08_semantic_composition_falsifier.json`](../successor-corpus/development-receipts/08_semantic_composition_falsifier.json) | `8cdcaea25fcd4e0735ea1081cbb19fb000e270c81312cc31a9bba4316631a250` |
| R11 | Later whole-event replication | [`../successor-corpus/development-receipts/11_event_cluster_process_uncertainty.json`](../successor-corpus/development-receipts/11_event_cluster_process_uncertainty.json) | `aebb42800f7a63678993f8608a4bd39f7c6fbeb8fd2f74b0d90c8cc5698e11bb` |
| R13 | Frozen no-refit complete-law replay | [`../successor-corpus/development-receipts/13_frozen_process_successor_replay.json`](../successor-corpus/development-receipts/13_frozen_process_successor_replay.json) | `dc48119c03b492217c3ab26ae781aaf1e6a5a87342d772cbcb78057095940e13` |
| R17 | Frozen no-refit continuous arrival-hazard replay | [`../successor-corpus/development-receipts/17_frozen_arrival_hazard_successor_replay.json`](../successor-corpus/development-receipts/17_frozen_arrival_hazard_successor_replay.json) | `0ffda46feea1e16ea9398ac9054ad70bc5b7cc1992874926b6b4e6abdbb8843f` |

## Claim map

| Manuscript claim | Evidence IDs | Status boundary |
|---|---|---|
| Registered samples are sticky, heavy-tailed, reversing, and sub-diffusive | E01, E10, E11, E15, R01, R11 | Descriptive development, fixed representation robustness, plus unchanged later replication |
| Boundaries, probability coordinates, maturity, and the one-hour clock do not individually explain the process signatures | E15 | Fixed development robustness; not independent replication |
| Quiet duration predicts update arrival | E03, E10, E11, E16, R11, R17 | Chronological development, exact freeze, measurement evidence, and frozen later replay |
| A frozen continuous staleness hazard improves absolute and relative next-update prediction on the later cohort | E16, R17 | Development-selected model plus no-refit later replay; not protected |
| The descended continuous hazard passes governed sparse formal development and is frozen | E14, E18 | New formal candidate passes; coarse-cell ancestor remains rejected; protected unexposed |
| State/path features improve sign and magnitude predictions | E04, E05 | Development only |
| Full hurdle law beats diffusion and simpler hurdle laws | E12, R13 | Development plus frozen no-refit later replication |
| Sparse formal arrival compression is not eligible for freeze | E14 | Formal development rejection |
| No protected or tradability claim is authorized | E01–E18, R01–R17 | `protected_values_exposed=false`; no protected run |

## Corpus identities

- Main expanded snapshot:
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`.
- Exact ancestor:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Later successor:
  `polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`.
- Main fresh/embargo/protected partition:
  `2144b8338515271f342738c3ed7ad62565d98343c3e3284353780b436fbd9a40`.
- Successor partition:
  `f7b47ea95c3630f083552bce84126711fb1a23b20ec7caa33e7527ba977586d7`.
