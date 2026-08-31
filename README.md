# lnk_builder

*Русская версия: [README.ru.md](README.ru.md)*

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

## Building `.lnk` shortcuts, step by step

`.lnk` is the flagship link type: unlike symlink/hardlink/junction, it's a
self-contained binary format, so `lnk_builder` builds it the same way no
matter which OS the build itself runs on. It does so through
[`pylnk3`](https://pypi.org/project/pylnk3/), a pure-Python reader/writer
for the format — no Windows API, no `pywin32`, no COM.

### Step 1 — install the `lnk` extra

```bash
pip install -e ".[lnk]"     # or ".[all]" for every backend
```

Confirm it landed:

```bash
lnk-builder doctor
# ...
# pylnk3 (lnk backend): installed
```

### Step 2 — write a minimal config

Only `type`, `target` and `link_path` are required. `target` must be in
**Windows notation** even if you're building from Linux/macOS — see
[the gotcha below](#windows-path-notation-is-mandatory).

```yaml
# shortcut.yaml
version: 1
links:
  - type: lnk
    target: "C:\\Program Files\\MyApp\\app.exe"
    link_path: "./MyApp.lnk"
```

### Step 3 — validate before writing anything

```bash
lnk-builder validate shortcut.yaml
# [OK] lnk: ./MyApp.lnk — validated (dry run, nothing written)
```

`validate` runs every backend's precondition checks (including the
Windows-path-notation check) without touching the filesystem.

### Step 4 — build it

```bash
lnk-builder build shortcut.yaml
# [OK] lnk: ./MyApp.lnk — .lnk shortcut created
```

### Step 5 — verify the result

On Linux/macOS, `file` independently recognizes the format:

```bash
$ file MyApp.lnk
MyApp.lnk: MS Windows shortcut, ... window=normal, ...
```

Or inspect it programmatically with the same library that wrote it:

```python
import pylnk3

shortcut = pylnk3.parse("MyApp.lnk")
print(shortcut.arguments, shortcut.description, shortcut.icon, shortcut.hot_key)
```

### A full example with every field

```yaml
version: 1
links:
  - type: lnk                                    # required — selects this backend
    target: "C:\\Program Files\\MyApp\\app.exe"   # required — Windows-notation path
    link_path: "C:\\Users\\me\\Desktop\\MyApp.lnk"  # required — must end in .lnk yourself
    platform: auto                                # accepted, but ignored (see notes below)
    overwrite: true                                # replace link_path if it exists
    arguments: "--start-minimized"                 # command-line arguments
    description: "Launch MyApp"                    # tooltip / shortcut description
    working_directory: "C:\\Program Files\\MyApp"  # startup ("Start in") directory
    icon_location: "C:\\Program Files\\MyApp\\app.exe"  # icon source file
    icon_index: 0                                  # icon index inside that file
    window_style: Normal                           # Normal | Maximized | Minimized
    hotkey: "CONTROL+ALT+M"                        # global shortcut key
```

#### Field reference

| Field | Required | Type / allowed values | Default | What it does |
|---|---|---|---|---|
| `type` | yes | `lnk` | — | Selects the `.lnk` backend. |
| `target` | yes | Windows-notation string: `C:\...` or UNC `\\server\share\...` | — | What the shortcut launches. Validated to *look like* a Windows path before anything is written; it does **not** need to exist on the machine running the build — `pylnk3` builds the shell item ID list straight from the string, which is exactly what makes cross-platform generation possible. |
| `link_path` | yes | any path on the machine running the build (POSIX or Windows notation, whichever your OS uses) | — | Where the `.lnk` file is written. Used exactly as given — `lnk_builder` does **not** append a `.lnk` extension for you, so include it yourself (Explorer relies on it to recognize the file as a shortcut). |
| `platform` | no | `auto` \| `windows` \| `linux` \| `macos` | `auto` | Accepted for schema consistency with the other link types, but the `lnk` backend's `validate()` never reads it — `.lnk` generation is always cross-platform, so this field has **no effect** here (unlike `symlink`/`hardlink`/`junction`, where it's enforced). Safe to omit. |
| `overwrite` | no | `true` \| `false` | `false` | Replace `link_path` if a file already exists there; otherwise the build fails with `LinkAlreadyExistsError` (or use `--force` on the whole config instead). |
| `arguments` | no | string | *(none)* | Command-line arguments appended when the shortcut is launched. |
| `description` | no | string | *(none)* | The shortcut's tooltip/description text (shown by Explorer). |
| `working_directory` | no | Windows-notation string | *(none)* | The "Start in" directory the target is launched with. Validated the same way as `target`. |
| `icon_location` | no | Windows-notation string | *(none, falls back to the target's own icon)* | Path to the file the icon is read from — typically the same `.exe`, or a dedicated `.ico`/`.dll`. Validated the same way as `target`. |
| `icon_index` | no | integer | `0` | Index of the icon *inside* `icon_location`, for files that bundle several icons (an `.exe`/`.dll` resource, or a multi-image `.ico`). `0` is the first/only icon. |
| `window_style` | no | exactly one of `Normal`, `Maximized`, `Minimized` (case-sensitive) | `Normal` | The window state the target is launched in. |
| `hotkey` | no | `"<modifier>[+<modifier>]+<key>"`, e.g. `"CONTROL+ALT+M"` | *(none)* | A global keyboard shortcut that activates this `.lnk`. Modifiers: `CONTROL`, `ALT`, `SHIFT` only — **not** `CTRL`. Key: `0`-`9`, `A`-`Z`, `F1`-`F24`, `NUM LOCK` or `SCROLL LOCK`. Checked upfront, so a typo fails at `validate`/`build` time with a clear message rather than a cryptic error mid-write. |

### Building from the Python library instead of the CLI

```python
from lnk_builder import LnkSpec, build_link

spec = LnkSpec(
    type="lnk",
    target=r"C:\Program Files\MyApp\app.exe",
    link_path=r"C:\Users\me\Desktop\MyApp.lnk",
    arguments="--start-minimized",
    description="Launch MyApp",
    window_style="Maximized",
)
result = build_link(spec)
print(result.ok, result.message)
```

### Windows path notation is mandatory

`target`, `icon_location` and `working_directory` must look like
`C:\...` or a UNC path `\\server\share\...` — this is what `pylnk3`
expects internally to build the shell item ID list, and `lnk_builder`
validates it upfront:

```yaml
links:
  - type: lnk
    target: /opt/app/tool          # ✗ POSIX path — rejected
    link_path: "./tool.lnk"
```

```text
$ lnk-builder validate shortcut.yaml
[FAIL] lnk: ./tool.lnk — target='/opt/app/tool' does not look like a
Windows path. lnk files need Windows notation, e.g. 'C:\Apps\tool.exe'...
```

There is no automatic POSIX-to-Windows translation — write the Windows
path literally, as the shortcut will need it on the machine that runs it.

### Rebuilding / overwriting a shortcut

Re-running `build` on an existing `link_path` fails by default
(`LinkAlreadyExistsError`). Either set `overwrite: true` on that entry, or
pass `--force` to replace every link in the config in one go:

```bash
lnk-builder build shortcut.yaml --force
```

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
