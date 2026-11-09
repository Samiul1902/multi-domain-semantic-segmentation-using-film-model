# POST-PHASE-13 H2-A-B1 — SELECTION REPLAY VERIFICATION

- status: **PASS**
- replay rule: strict lexicographic > on the frozen 6-term tuple; ties = BAD_EPOCH; patience 15

| quantity | replayed | stored |
|---|---|---|
| best epoch | 83 | 83 |
| final bad_epochs | 15 | 0 |
| early-stop epoch | 98 | — |

**best tuple (replayed):**
```
[0.4522162369629855, 0.6944444444444444, 0.6381578947368421, 0.2757111597374179, -0.0047946270615735, -1.842576136955848]
```
**best tuple (stored):**
```
[0.4522162369629855, 0.6944444444444444, 0.6381578947368421, 0.27571115973741794, -0.0047946270615735415, -1.8425761369558482]
```

**mismatches: 0**
