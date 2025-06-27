# OTR bot

-----

**Table of Contents**

- [Installation](#installation)
- [Használati útmutató](#Használati)
- [License](#license)

## Create portable installation

### Hozd létre a portable struktúrát

```console
mkdir otrbot-portable
mkdir otrbot-portable\app
mkdir otrbot-portable\python

REM Másold át a wheel fájlt
copy dist\otrbot-0.1.0-py3-none-any.whl otrbot-portable\app\

REM Másold át a main.py-t
copy src\main.py otrbot-portable\app\

REM Másold át a .env fájlt (ha van)
copy .env otrbot-portable\app\
```

### Töltsd le az embedded Python-t

- Menj a https://www.python.org/downloads/windows/ oldalra
- Töltsd le a "Windows embeddable package (64-bit)" verziót
- Csomagold ki a otrbot-portable\python\ mappába

## Használati útmutató
- Csomagold ki a otrbot-portable mappát bárhova
- Futtasd az install.cmd-t (csak egyszer)
- Használd a run.cmd-t: run.cmd -s "Benyújtás" -f "data.xlsx" -sp "BM"

## License

`otrbot` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
