# CSS validation report

Generated on 02 October 2026 at 01:52. `static/css/style.css` was uploaded to the [W3C CSS Validation Service](https://jigsaw.w3.org/css-validator/) (profile: CSS level 3 + SVG, all warnings):

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
| 91 | Due to their dynamic nature, CSS variables are currently not statically checked | Expected: the design tokens (colours, spacing, fonts) are custom properties, which the validator doesn't check. | 144, 178, 187, 208, 241, 319, 443, 573, 655, 675, 713, 755, 769, 828, 873, 1027, 1075, 1136, 1178, 1184, 1193, 1299, 1352, 1368, 1369, 1528, 1534, 1553, 1641, 1647, 1655, 1689, 1751, 1787, 1817, 1985, 2033, 2055, 2090, 2188, 2265, 2312, 2451, 2532, 2592, 2603, 2664, 2755, 2784, 2891, 2928, 2999, 3014, 3153, 3343, 3443, 3471, 3540, 3601, 3641, 3783, 3784, 3816, 3820, 3849, 3910, 3970, 3986, 4062, 4163, 4255, 4282, 4309, 4344, 4360, 4412, 4440, 4520, 4610, 4641, 4643, 4686, 4780, 4803, 4827, 4927, 4975, 5000, 5005, 5029, 5060 |
| 3 | “::-webkit-scrollbar” is a vendor extended pseudo-element | Expected: hides the scrollbar of the sideways carousels and tab bars in Chrome and Safari. | 744, 1420, 1719 |
| 2 | Same color for “background-color” and “border-color” | Intentional: the current page in the pagination has the same fill and border colour. | 578, 578 |
| 2 | “::-webkit-details-marker” is a vendor extended pseudo-element | Expected: hides the default triangle on the mobile Country menu (`<details>`) in Safari. | 822, 4511 |
| 2 | “-webkit-box” is a vendor extension | Expected: required by `-webkit-line-clamp`. | 1270, 1306 |
| 2 | “-webkit-line-clamp” is a vendor extension | Expected: the prefixed line clamp is the standard way to cut card text to 1–2 lines; every browser supports it. | 1271, 1307 |
| 2 | “-webkit-box-orient” is a vendor extension | Expected: required by `-webkit-line-clamp`. | 1272, 1308 |
| 2 | “-ms-overflow-style” is a vendor extension | Expected: hides the same scrollbars in older Edge. | 1424, 1723 |
| 1 | “-webkit-text-size-adjust” is a vendor extension | Expected: stops iOS Safari enlarging text when a phone is turned sideways. | 139 |
