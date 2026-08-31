# lnk_builder

Cross-platform builder for links and shortcuts, driven by a single YAML/JSON
config: **symlinks**, **hardlinks**, **Windows junctions**, **Windows `.lnk`
shortcuts** and **macOS alias files**.

The key feature: `.lnk` and macOS alias files are true binary file formats,
so `lnk_builder` can generate them **from any OS** — build a Windows
shortcut or a Mac alias from a Linux CI runner, without touching a Windows
or macOS API. Symlinks, hardlinks and junctions, on the other hand, are
records inside a specific filesystem rather than portable files — those can
only ever be created natively, on the OS that will host them (see
[Limitations](#limitations) below).

## Support matrix

| Link type | From Linux | From Windows | From macOS |
|---|---|---|---|
| `symlink`  | Linux targets only | Windows targets only | macOS targets only |
| `hardlink` | Linux targets only, same filesystem | Windows targets only, same filesystem | macOS targets only, same filesystem |
| `junction` | no (experimental descriptor only) | yes, native | n/a |
| `lnk`      | yes | yes (native or generated) | yes |
| `alias`    | yes, best-effort | yes, best-effort | yes, most reliable |

## Install

```bash
pip install -e ".[all]"     # everything (pylnk3 + mac_alias)
pip install -e ".[lnk]"     # only the .lnk backend
pip install -e ".[alias]"   # only the alias backend
pip install -e .            # symlink/hardlink/junction only
```

## Quick start

```bash
lnk-builder init links.yaml   # write an example config
lnk-builder validate links.yaml
lnk-builder build links.yaml
```

Example `links.yaml`:

```yaml
version: 1

defaults:
  overwrite: false
  platform: auto

links:
  - type: symlink
    target: /opt/app/bin/tool
    link_path: /usr/local/bin/tool

  - type: lnk
    target: "C:\\Program Files\\MyApp\\app.exe"
    link_path: "C:\\Users\\me\\Desktop\\MyApp.lnk"
    arguments: "--start-minimized"
    description: "Launch MyApp"
    working_directory: "C:\\Program Files\\MyApp"
    icon_location: "C:\\Program Files\\MyApp\\app.exe"
    window_style: Normal

  - type: alias
    target: /Applications/MyApp.app
    link_path: "/Users/me/Desktop/MyApp alias"
    volume_name: "Macintosh HD"
```

See [`examples/links.example.yaml`](examples/links.example.yaml) for every
field, including `hardlink`, `junction` and hotkeys.

## CLI reference

- `lnk-builder build CONFIG [--force] [--dry-run] [--continue-on-error]` —
  create every link in `CONFIG`.
- `lnk-builder validate CONFIG` — check the config and every link's
  preconditions without writing anything.
- `lnk-builder init [CONFIG] [--force]` — write an example config file.
- `lnk-builder doctor` — report what the current OS/process can actually
  build (symlink privileges, junction support, installed backends).

## Library usage

```python
from lnk_builder import build_all
from lnk_builder.config import load_config

config = load_config("links.yaml")
report = build_all(config.links, continue_on_error=True)
for result in report:
    print(result.ok, result.link_path, result.message)
```

## Configuration reference

Top-level keys: `version`, `defaults` (`overwrite`, `platform`), `links`
(a list of link specs). Every link entry supports:

- `type`: `symlink` | `hardlink` | `junction` | `lnk` | `alias`
- `target`: what the link points at
- `link_path`: where the link/shortcut is created
- `platform`: `auto` (default) | `windows` | `linux` | `macos`
- `overwrite`: replace `link_path` if it already exists (default `false`)

Type-specific fields:

- `symlink`: `target_is_directory` (optional hint used on Windows)
- `junction`: `emit_descriptor_when_unavailable` (experimental, see below)
- `lnk`: `arguments`, `description`, `working_directory`, `icon_location`,
  `icon_index`, `window_style` (`Normal`/`Maximized`/`Minimized`), `hotkey`
  (e.g. `"CONTROL+ALT+M"`)
- `alias`: `volume_name`, `volume_uuid`, `volume_path`,
  `best_effort_finder_flag`

`.lnk` `target`/`icon_location`/`working_directory` must be given in
**Windows notation** (`C:\...` or a UNC path `\\server\share\...`) even
when generating from Linux/macOS — there is no automatic POSIX-to-Windows
path translation, only validation that the string looks like one.

## Limitations

- **Hardlinks cannot be generated cross-platform, at all.** A hardlink is
  a second directory entry pointing at the same inode/MFT record — there
  is no byte sequence to write from Linux that becomes a real hardlink on
  a Windows/NTFS volume. `platform` must match the OS the build runs on,
  or the build fails fast with `CrossPlatformNotSupportedError`.
- **Junctions are native-Windows-only** in the primary code path, for the
  same reason (an NTFS reparse point needs a real NTFS volume and the
  Windows I/O manager). Setting `emit_descriptor_when_unavailable: true`
  writes an experimental `*.reparse.json` side-car describing the
  junction instead of failing — it is **not** a working junction by
  itself and must be applied later on an actual Windows host.
- **Alias files are best-effort outside macOS.** The bookmark byte format
  is generated correctly and is readable cross-platform, but real Catalog
  Node IDs, volume UUID and creation dates are macOS-only information;
  generated aliases use synthetic placeholders, so Finder falls back to
  path-based (rather than ID-based) resolution. The Finder "is alias"
  flag (`com.apple.FinderInfo` xattr) is set opportunistically and may
  not survive a non-Mac-aware copy (plain `cp`, generic zip, git, ...).
  **Verify generated aliases on a real Mac before relying on them in
  production.**
- Windows symlinks require Developer Mode or an elevated process; run
  `lnk-builder doctor` to check.

## License

MIT — see [`LICENSE`](LICENSE). Third-party dependency licenses (LGPL for
`pylnk3`, MIT for `mac_alias`) are noted in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
