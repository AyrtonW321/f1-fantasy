# Chip backtest 2023-2026 (hindsight, robust_mu team)

Mean points a chip would have added in a round. 2026 chip rules used for every season.
Wildcard counts its round plus the next 2. Final Fix not replayed (rule backtest: +51 over 18 swaps, 2026).

## Overall and sprint vs normal

```text
        limitless  x3_boost  no_negative  autopilot  wildcard
sprint                                                       
False        73.0      47.0         15.2        3.1       0.8
True         76.7      54.5         23.9        3.5       3.5
```

Overall: limitless 74.0, x3_boost 49.1, no_negative 17.5, autopilot 3.2, wildcard 1.6

## Wildcard by round

```text
round
(0, 6]      10.9
(6, 12]      0.0
(12, 18]     0.0
(18, 25]    -4.3
```

## Best tracks per chip (mean over seasons)

- limitless: chinese-grand-prix 184, japanese-grand-prix 124, miami-grand-prix 116, singapore-grand-prix 102, bahrain-grand-prix 96, saudi-arabian-grand-prix 96
- x3_boost: chinese-grand-prix 82, miami-grand-prix 81, spanish-grand-prix 75, emilia-romagna-grand-prix 74, austrian-grand-prix 68, abu-dhabi-grand-prix 66
- no_negative: las-vegas-grand-prix 33, united-states-grand-prix 32, monaco-grand-prix 31, australian-grand-prix 30, qatar-grand-prix 25, barcelona-grand-prix 24
- autopilot: barcelona-grand-prix 14, azerbaijan-grand-prix 13, chinese-grand-prix 12, las-vegas-grand-prix 10, miami-grand-prix 9, canadian-grand-prix 9
- wildcard: chinese-grand-prix 62, monaco-grand-prix 25, bahrain-grand-prix 18, saudi-arabian-grand-prix 15, australian-grand-prix 10, miami-grand-prix 6
