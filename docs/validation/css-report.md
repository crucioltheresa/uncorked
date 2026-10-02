# CSS validation report

Generated on 02 October 2026 at 11:02. `static/css/style.css` was uploaded to the [W3C CSS Validation Service](https://jigsaw.w3.org/css-validator/) (profile: CSS level 3 + SVG, all warnings):

```
curl -F "file=@static/css/style.css;type=text/css" -F output=json \
     -F profile=css3svg -F warning=1 \
     https://jigsaw.w3.org/css-validator/validator
```

| File | Valid | Errors | Warnings |
| --- | --- | ---: | ---: |
| `static/css/style.css` | Yes | 0 | 107 |

## Errors

No errors.

## Warnings by kind

Warnings don't make the stylesheet invalid. Each kind below is expected; the reason is given next to it.

| Count | Warning | Why it's expected | Lines |
| ---: | --- | --- | --- |
| 91 | Due to their dynamic nature, CSS variables are currently not statically checked | Expected: the design tokens (colours, spacing, fonts) are custom properties, which the validator doesn't check. | 144, 178, 187, 208, 241, 319, 443, 573, 655, 675, 713, 755, 769, 828, 873, 1027, 1082, 1143, 1185, 1191, 1200, 1306, 1359, 1375, 1376, 1535, 1541, 1560, 1648, 1654, 1662, 1696, 1758, 1794, 1824, 1992, 2040, 2062, 2097, 2195, 2272, 2319, 2458, 2539, 2599, 2610, 2671, 2762, 2791, 2898, 2935, 3006, 3021, 3160, 3350, 3450, 3478, 3547, 3608, 3648, 3790, 3791, 3823, 3827, 3856, 3917, 3977, 3993, 4069, 4170, 4262, 4289, 4316, 4351, 4367, 4419, 4447, 4527, 4617, 4648, 4650, 4693, 4787, 4810, 4834, 4934, 4982, 5007, 5012, 5036, 5067 |
| 3 | “::-webkit-scrollbar” is a vendor extended pseudo-element | Expected: hides the scrollbar of the sideways carousels and tab bars in Chrome and Safari. | 744, 1427, 1726 |
| 2 | Same color for “background-color” and “border-color” | Intentional: the current page in the pagination has the same fill and border colour. | 578, 578 |
| 2 | “::-webkit-details-marker” is a vendor extended pseudo-element | Expected: hides the default triangle on the mobile Country menu (`<details>`) in Safari. | 822, 4518 |
| 2 | “-webkit-box” is a vendor extension | Expected: required by `-webkit-line-clamp`. | 1277, 1313 |
| 2 | “-webkit-line-clamp” is a vendor extension | Expected: the prefixed line clamp is the standard way to cut card text to 1–2 lines; every browser supports it. | 1278, 1314 |
| 2 | “-webkit-box-orient” is a vendor extension | Expected: required by `-webkit-line-clamp`. | 1279, 1315 |
| 2 | “-ms-overflow-style” is a vendor extension | Expected: hides the same scrollbars in older Edge. | 1431, 1730 |
| 1 | “-webkit-text-size-adjust” is a vendor extension | Expected: stops iOS Safari enlarging text when a phone is turned sideways. | 139 |
