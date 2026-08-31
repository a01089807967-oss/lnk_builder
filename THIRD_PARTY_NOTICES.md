# Third-party notices

`lnk_builder` itself is MIT-licensed (see `LICENSE`). It depends, as
optional extras, on the following third-party packages:

## pylnk3

- Used by: `lnk_builder.backends.lnk` (the `lnk` link type)
- License: LGPL
- Source: https://pypi.org/project/pylnk3/

`pylnk3` is used unmodified as a regular pip dependency (dynamically
linked, in FOSS-license terms), which does not impose LGPL obligations on
`lnk_builder`'s own MIT license. If you vendor or modify `pylnk3` itself,
you take on LGPL's copyleft obligations for that modified copy.

## mac_alias

- Used by: `lnk_builder.backends.alias` (the `alias` link type)
- License: MIT
- Source: https://pypi.org/project/mac_alias/

No additional obligations beyond attribution.
