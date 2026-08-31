# lnk_builder

*English version: [README.md](README.md)*

Кроссплатформенный билдер ссылок и ярлыков, управляемый одним
YAML/JSON-конфигом: **символические ссылки (symlink)**, **жёсткие ссылки
(hardlink)**, **Windows junction points**, **Windows-ярлыки `.lnk`** и
**alias-файлы macOS**.

Ключевая особенность: `.lnk` и alias-файлы macOS — это самостоятельные
бинарные форматы файлов, поэтому `lnk_builder` умеет генерировать их
**с любой ОС** — можно собрать Windows-ярлык или Mac-алиас прямо на
Linux CI-раннере, не обращаясь ни к Windows, ни к macOS API. Symlink,
hardlink и junction, напротив, — это записи внутри конкретной файловой
системы, а не переносимые файлы, поэтому создаются только нативно, на
той ОС, где будут использоваться (подробнее — в разделе
[«Ограничения»](#ограничения)).

## Возможности

`lnk_builder` умеет создавать пять типов ссылок, каждая — со своим
backend-модулем и своим набором настроек в конфиге.

### 1. Символические ссылки (`symlink`)

Обычный `os.symlink` — работает на Linux, macOS и Windows, но **только
нативно**, то есть с той ОС, для которой создаётся ссылка. Поддерживает:

- указание, что цель — директория (`target_is_directory`), это нужно
  Windows API, если сама цель ещё не существует на диске;
- флаг `overwrite` — заменить `link_path`, если он уже занят;
- на Windows перед созданием билдер сам проверяет права: нужен либо
  Developer Mode, либо запуск от администратора — при их отсутствии
  выдаётся понятная ошибка вместо невнятного `OSError`.

### 2. Жёсткие ссылки (`hardlink`)

`os.link` — вторая запись в таблице inode (POSIX) или MFT (NTFS),
указывающая на тот же файл. Тоже только нативно. Билдер заранее
проверяет типичные ошибки и сообщает о них понятным текстом до попытки
записи:

- цель — директория → жёсткие ссылки на директории не поддерживаются
  ни POSIX, ни NTFS через штатный API;
- цель и `link_path` на разных томах/файловых системах (`EXDEV`) →
  подсказка использовать symlink вместо hardlink;
- цель не существует → ошибка `TargetNotFoundError` ещё до записи.

### 3. Windows junction points (`junction`)

NTFS reparse point для директорий. На Windows создаётся нативно через
`_winapi.CreateJunction` (без прав администратора), с фолбэком на
`mklink /J`, если этот API недоступен в интерпретаторе.

Вне Windows полноценный junction создать невозможно — для этого нужен
реальный NTFS-том и Windows I/O Manager. Но если в конфиге включить
`emit_descriptor_when_unavailable: true`, билдер запишет
**экспериментальный** сайдкар-файл `<link_path>.reparse.json` с описанием
будущего junction — не рабочую ссылку, а инструкцию, которую нужно
применить позже уже на настоящей Windows-машине (например, той же
командой `mklink /J`).

### 4. Ярлыки Windows `.lnk`

Полностью кроссплатформенная генерация через библиотеку `pylnk3` —
чистый Python без единого системного вызова, поэтому `.lnk`-файл
одинаково корректно собирается что на Windows, что на Linux или macOS.
Настраиваются:

- `arguments` — аргументы командной строки;
- `description` — описание ярлыка;
- `working_directory` — рабочая директория запуска;
- `icon_location` + `icon_index` — путь к иконке и её индекс в файле;
- `window_style` — `Normal` / `Maximized` / `Minimized`;
- `hotkey` — комбинация клавиш вида `"CONTROL+ALT+M"`.

Важно: `target`/`icon_location`/`working_directory` для `.lnk` должны
быть заданы в **Windows-нотации** (`C:\...` или UNC `\\server\share\...`)
даже при генерации с Linux/macOS — автоматического перевода
POSIX-путей в Windows-пути нет, билдер только проверяет, что строка
уже выглядит как Windows-путь, и явно откажется собирать файл, если
формат не совпадает.

### 5. Alias-файлы macOS

Тоже кроссплатформенная генерация, через библиотеку `mac_alias` —
собирается тот же bookmark-формат, который использует современный
Finder («Сделать алиас»). Настраиваются:

- `volume_name` — имя тома-источника (по умолчанию `"Macintosh HD"`);
- `volume_uuid` — реальный UUID тома, если он известен;
- `volume_path` — точка монтирования тома (по умолчанию `/`);
- `best_effort_finder_flag` — попытаться выставить у файла Finder-флаг
  «это алиас» через расширенный атрибут `com.apple.FinderInfo`.

Это **best-effort вне macOS**: сам бинарный формат bookmark собирается
корректно и одинаково читается любой ОС, но некоторые поля — реальные
Catalog Node ID (CNID), настоящий UUID тома, даты создания — доступны
только через сисколы самой macOS. Если не заданы вручную, они
заполняются синтетическими плейсхолдерами, поэтому Finder распознаёт
такой алиас по пути, а не по внутренним ID (что по-прежнему работает
корректно, пока путь на целевом Маке верный). Перед использованием в
проде такие алиасы стоит проверить на настоящем Mac.

### Общая инфраструктура

- **Единый конфиг** — весь список ссылок описывается одним YAML/JSON-
  файлом, значения по умолчанию (`overwrite`, `platform`) задаются один
  раз в `defaults` и наследуются каждой ссылкой, с возможностью
  переопределить их точечно.
- **Валидация до записи** — каждый backend проверяет свои условия
  (`validate()`) прежде, чем что-либо создавать, поэтому ошибки
  конфигурации ловятся сразу и с понятным текстом, а не после половины
  работы.
- **Пакетная сборка с отчётом** — `build_all()`/CLI `build` создают все
  ссылки разом и возвращают отчёт по каждой (успех/ошибка), с
  флагом `--continue-on-error`, чтобы не останавливаться на первой же
  неудаче.
- **Сухой прогон** — `--dry-run`/`lnk-builder validate` проверяют все
  предусловия, не создавая ни одного файла.
- **`lnk-builder doctor`** — диагностика: какие возможности реально
  доступны на текущей ОС (права на symlink на Windows, поддержка
  junction API, установлены ли `pylnk3`/`mac_alias`).
- **CLI и библиотека** — всё доступно и как консольная команда
  `lnk-builder`, и как обычный Python-пакет `import lnk_builder`.

## Таблица поддержки по ОС

| Тип ссылки | С Linux | С Windows | С macOS |
|---|---|---|---|
| `symlink`  | только Linux-цели | только Windows-цели | только macOS-цели |
| `hardlink` | только Linux-цели, тот же том | только Windows-цели, тот же том | только macOS-цели, тот же том |
| `junction` | нет (только экспериментальный дескриптор) | да, нативно | н/д |
| `lnk`      | да | да (нативно или генерацией) | да |
| `alias`    | да, best-effort | да, best-effort | да, наиболее надёжно |

## Установка

```bash
pip install -e ".[all]"     # всё сразу (pylnk3 + mac_alias)
pip install -e ".[lnk]"     # только backend для .lnk
pip install -e ".[alias]"   # только backend для alias
pip install -e .            # только symlink/hardlink/junction
```

## Быстрый старт

```bash
lnk-builder init links.yaml   # записать пример конфига
lnk-builder validate links.yaml
lnk-builder build links.yaml
```

Пример `links.yaml`:

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

Полный список полей — включая `hardlink`, `junction` и hotkey — смотрите
в [`examples/links.example.yaml`](examples/links.example.yaml).

## Справочник CLI

- `lnk-builder build CONFIG [--force] [--dry-run] [--continue-on-error]` —
  создать все ссылки из `CONFIG`.
- `lnk-builder validate CONFIG` — проверить конфиг и предусловия каждой
  ссылки, ничего не записывая.
- `lnk-builder init [CONFIG] [--force]` — записать пример конфига.
- `lnk-builder doctor` — показать, что реально может собрать текущая
  ОС/процесс (права на symlink, поддержка junction, установленные
  backend-пакеты).

## Использование как библиотеки

```python
from lnk_builder import build_all
from lnk_builder.config import load_config

config = load_config("links.yaml")
report = build_all(config.links, continue_on_error=True)
for result in report:
    print(result.ok, result.link_path, result.message)
```

## Справочник конфигурации

Ключи верхнего уровня: `version`, `defaults` (`overwrite`, `platform`),
`links` (список описаний ссылок). Общие поля каждой ссылки:

- `type`: `symlink` | `hardlink` | `junction` | `lnk` | `alias`
- `target`: на что указывает ссылка
- `link_path`: где создаётся ссылка/ярлык
- `platform`: `auto` (по умолчанию) | `windows` | `linux` | `macos`
- `overwrite`: заменить `link_path`, если он уже существует (по
  умолчанию `false`)

Специфичные поля по типам:

- `symlink`: `target_is_directory` (необязательная подсказка для
  Windows)
- `junction`: `emit_descriptor_when_unavailable` (экспериментально, см.
  выше)
- `lnk`: `arguments`, `description`, `working_directory`,
  `icon_location`, `icon_index`, `window_style`
  (`Normal`/`Maximized`/`Minimized`), `hotkey` (например,
  `"CONTROL+ALT+M"`)
- `alias`: `volume_name`, `volume_uuid`, `volume_path`,
  `best_effort_finder_flag`

## Ограничения

- **Жёсткие ссылки нельзя сгенерировать кроссплатформенно — вообще
  никак.** Hardlink — это вторая запись в таблице inode/MFT, указывающая
  на тот же файл, а не набор байт, который можно записать в файл. Нет
  такой последовательности байт, которую можно было бы записать с
  Linux и получить настоящий hardlink на Windows/NTFS-томе. Поле
  `platform` обязано совпадать с ОС, на которой реально запускается
  сборка — иначе билдер сразу и явно откажет с
  `CrossPlatformNotSupportedError`, вместо невнятной ошибки ОС.
- **Junction — только нативно на Windows** в основном сценарии, по той
  же причине (NTFS reparse point требует реального NTFS-тома и Windows
  I/O Manager). Флаг `emit_descriptor_when_unavailable: true` вместо
  отказа пишет экспериментальный сайдкар `*.reparse.json` с описанием
  junction — это **не** рабочая ссылка сама по себе, её нужно применить
  позже на настоящей Windows-машине.
- **Alias-файлы — best-effort вне macOS.** Байтовый формат bookmark
  собирается корректно и одинаково читается на любой ОС, но настоящие
  Catalog Node ID, UUID тома и даты создания — это информация,
  доступная только через сисколы самой macOS; в сгенерированных алиасах
  вместо них — синтетические плейсхолдеры, поэтому Finder распознаёт
  такой файл по пути, а не по внутренним ID. Finder-флаг «это алиас»
  (xattr `com.apple.FinderInfo`) выставляется по возможности и может не
  пережить копирование не-Mac-совместимым способом (обычный `cp`,
  типовой zip, git и т. п.). **Перед использованием в продакшене
  проверяйте сгенерированные алиасы на настоящем Mac.**
- Windows-symlink требует Developer Mode или запуска с повышенными
  правами — проверить можно командой `lnk-builder doctor`.

## Лицензия

MIT — см. [`LICENSE`](LICENSE). Лицензии сторонних зависимостей (LGPL
для `pylnk3`, MIT для `mac_alias`) указаны в
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
