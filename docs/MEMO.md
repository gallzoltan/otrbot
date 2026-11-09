# OTR bot – munkamemó

Ez a fájl a fejlesztés állását rögzíti, hogy másik gépen (pl. otthon) is folytatható legyen. Claude: a munka elején olvasd el, a végén frissítsd.

Utolsó frissítés: 2026-11-09

## Mi volt a probléma

Egy támogatás három menete (Benyújtás → Döntés → Szerződés) együtt kb. 1 perc volt, így 2000 tétel több mint 30 óra. Csak felügyelettel lehetett futtatni, mert:
- egy hiba után a böngésző rossz állapotban maradt, és a további tételek is elhasaltak;
- nem volt feljegyezve, mi sikerült, ezért kézzel kellett kikeresni, honnan kell újraindítani.

## Mit csináltunk (2026-10-30)

### 1. Felügyelet nélküli futás
- **Napló** (`src/otrbot/journal.py`): `<excel>.journal.sqlite` az Excel mellett; minden (rowid, menet) eredménye `ok` / `failed` / `pending`. Újraindításkor csak a nem `ok` tételek futnak le.
- **Eredmény**: csak a SQLite napló (az `_eredmeny.xlsx` export megszűnt, lásd lent).
- **Retry és helyreállítás** (`runner.py`, `_run_item` / `_recover`): tételenként 2 próbálkozás; hiba után képernyőkép + HTML a `logs/fail/` mappába, oldal újratöltése, újrabelépés, szükség esetén a Firefox újraindítása. Ha 10 tétel egymás után hibás, a futás leáll.
- **Strict mód**: a `WebDriver.strict = True` miatt az első sikertelen lépés `StepFailed` kivételt dob, és a tételt azonnal feladja.
- **Duplikáció elleni védelem**: ha a végső „… kész” gombot már megerősítette, de nem jött siker-üzenet, a bot NEM próbálja újra (`FinalSubmitError` / `SubmittedUncertain`, „BIZONYTALAN” jelzés a naplóban).
- **Kapcsolók**: `--headless`; a `-b/-e` a `rowid` oszlopra szűr (korábban nem csinált semmit).
- **Logok**: futásonként külön fájl, `logs/otr_<időbélyeg>.log`; a log végén a 10 leglassabb lépés.

### 2. Gyorsítás
- Egy várakozás interakciónként, 0,05 mp-es pollinggal (a Selenium alapértéke 0,5 mp volt, és lépésenként 3 várakozás).
- `setValue` (JS) a hosszú szövegmezőkhöz: megnevezés, összefoglalás, cél.
- `readGrid` (JS): a keresés találati listáját egy hívással olvassa ki.
- Animációk tiltása, `selectOption` megvárja a betöltődő opciót.
- **`waitForPageIdle`**: minden fülkattintás után vár, amíg az AngularJS `$http` kérései befejeződnek. FONTOS: az app az `#otr_angular_inner` elemen fut (`ng-app="otrApplication"`), nem a `body`-n. E nélkül a Döntés fül aszinkron betöltése kiürítette a már kitöltött mezőket.

### 3. OTR azonosító
- A Benyújtás után az OTR azonosító **nem jelenik meg** a felületen, csak a „Támogatások listázása” keresőben.
- A Döntés menet, ha az Excel `otrid` oszlopa üres, a **konstrukció azonosító (`kid`) + adószám (`regid`)** alapján keres. A találatot a település neve, a státusz és az adószám első 8 jegye alapján választja ki, majd a találati lista **első oszlopából** elmenti az OTR azonosítót a naplóba. A Szerződés már erre keres.
- A találati lista oszlopai: 0 azonosító, 1 megnevezés, 2 státusz, 3 döntés dátuma, 4 igénylő neve, 5 igénylő adószáma, 6 konstrukció, 7 kizáró ok, 8 művelet (`models/search_table.py`).

### 4. Csak SQLite napló (2026-10-30)
- Az `_eredmeny.xlsx` export (`Journal.export`) megszűnt; egyetlen eredménytár a `<excel>.journal.sqlite`.
- Új `applicants` tábla (rowid, település, adószám): a `start()` tölti, így a napló az Excel nélkül is olvasható.
- `eredmeny` nézet: tételenként egy sor (`telepules`, `adoszam`, `otr_azonosito`, menetenként `_status`, `_probalkozas`, `_hiba`). Minden megnyitáskor újra létrejön, így a régi naplófájlokon is működik (ott a település/adószám üres, amíg a tétel újra el nem indul).
- A log végén a menet nem `ok` tételei soronként (`not ok id:… city:…: hiba`).
- Duplikáció elleni védelem: a Benyújtás kihagyja azokat a tételeket, amelyeknek már van OTR azonosítójuk (napló vagy Excel `otrid`). Ezek `ok` státuszt kapnak „Kihagyva, már van OTR azonosító” megjegyzéssel. Ok: a kézzel rögzített tételeket (pl. Abda, rowid 11) a felhasználó előre beírja az Excelbe. EDU-ban kipróbálva (rowid 11), működik. A rowid 11–20 mindhárom menete hibátlan volt: 7,8 / 7,5 / 4,6 mp/tétel. Benyújtás rowid 21–100 `--headless`: 80/80 ok, 7,4 mp/tétel, 10 perc, ebből ~1,5 mp/tétel a szerver válasza a „kész” gomb után (`catchError`). Döntés rowid 21–100 `--headless`: 80/80 ok, 8,4 mp/tétel, 11 perc; 80 különböző OTR azonosító a naplóban; a „Döntés kész” utáni szerverválasz ~3,2 mp/tétel. Szerződés rowid 21–100 `--headless`: 80/80 ok, 4,3 mp/tétel, 6 perc. A teszt Excel mind a 100 tétele mindhárom menetben `ok`, egyetlen újrapróbálkozás nélkül; egy tétel a három menetben összesen ≈ 20 mp.
- Átnézés: DB Browser for SQLite, vagy `sqlite3 data/x.journal.sqlite "select * from eredmeny"`.

### 5. Applicants előtöltés, egész rowid (2026-10-31)
- Az `applicants` tábla a betöltéskor (`load_datas` → `Journal.load_applicants`) egyszerre töltődik az Excel **összes** sorából (a `-b/-e` szűréstől függetlenül); az Excel felülírja a régi értéket. A `start()` már nem ír bele.
- Az `eredmeny` nézet minden Excel-sort mutat, a még el nem indított tételeknél üres státusszal (a napló olyan tételei is látszanak, amelyek nincsenek az Excelben).
- A `rowid` mindenhol INTEGER (`items`, `applicants`, `Master.rowid`); a régi, TEXT rowid-os naplókat megnyitáskor átépíti (`Journal._migrate`). A `be-tuzelo-teszt_2026.journal.sqlite` másolatán kipróbálva: a 100 `ok` tétel és az OTR azonosítók megmaradtak, a nézetben 2628 sor.
- Az Excelben az érvénytelen/üres rowid-ú sorokat a beolvasás kihagyja (figyelmeztetés a logban).
- Felmerült: a betöltő Excel helyett SQLite bemenet (az adatok egy PostgreSQL lekérdezésből jönnek). Egyelőre nem csináltuk meg.

### 6. Ablakméret, szerveres futtatás (2026-11-02)
- A headless Firefox alapból 1366×768-as ablakkal indult; a `HEADLESS_OPTIONS` Chrome-os `--window-size` kapcsolója hatástalan és nem is volt használva, ezért törölve. Helyette `WebDriverConfig.WINDOW_SIZE = (1920, 1080)`, amit a `WebDriver.__init__` a `set_window_size` hívással állít be (headless és normál módban is). Helyben kipróbálva: 1920×1080, a viewport 1920×994.
- A cél egy **AlmaLinux szerver grafikus felület nélkül**: `dnf install firefox dejavu-*-fonts`, geckodriver tarballból a `/usr/local/bin`-be, Python 3.12.10+ az `uv`-vel (`uv sync`), `.env`-ben `SYSTEM=linux`, futtatás `--headless`-szel `tmux`/`nohup` alatt.
- **Telepítő**: `scripts/install_almalinux.sh` (dnf csomagok, geckodriver a legújabb verzióval vagy `GECKODRIVER_VERSION`, uv + `uv sync --no-dev`, `src/.env` a mintából `SYSTEM=linux`, `ENV=dev`, chmod 600, a végén headless Firefox próba). Többször is futtatható. AlmaLinux 9.8 konténerben (podman, rootként) végigfutott, a próba 1920×1080-as ablakot adott. Buktató: az AlmaLinux 9 `curl-minimal`-t tartalmaz, ez ütközik a `curl` csomaggal, ezért a curl csak akkor települ, ha hiányzik. Valódi szerveren még nem próbáltuk.
- **Podman változat**: `Containerfile` (AlmaLinux 9, Firefox ESR, geckodriver 0.37.1, uv 0.13.6, Python 3.12.10 a `.python-version` alapján, `TZ=Europe/Budapest`, `SYSTEM=linux`) + `.containerignore` + `scripts/otrbot-podman.sh build|test|run|shell`. A `run` a `--headless`-t magától hozzáteszi; csatolások: `data/` → `/app/data` (Excel + napló), `logs/` → `/app/logs`, `src/.env` → `/app/src/.env` (ro); mind `:Z` (SELinux). Rootless podmannal a fájlok a futtató felhasználó tulajdonába kerülnek. Az Excel útvonala konténeren belüli: `-f data/<fájl>.xlsx`. Helyben (Ubuntu, podman 4.9) kipróbálva: build, headless Firefox 1920×1080, kilépési kód, log a gazdagépen, `.env` idézőjeles jelszóval. Buktató: a `.python-version` nélkül az uv újabb Pythont választott, és a numpy forrásból akart fordulni. Valódi OTR futás a konténerből még nem volt.
- Mellékmegfigyelés: a log időformátuma `%I` (12 órás, AM/PM nélkül) az `otr_logging.py`-ban; nem javítottuk.

### 7. Első éles Benyújtás kör, `-r/--rows` (2026-11-05)
- `data/be-tuzelo_2026.xlsx`, 2628 tétel: 2601 `ok`, 27 `failed`, kb. 5,8 mp/tétel.
- **25 tétel: `RogzitesKesz: A támogatási igény ellenőrzése 1 hibát talált!`** Az igénylő címéből hiányzik a Házszám (a felhasználó mind a 25-nél ezt találta; a cím az OTR-ből jön, nem az Excelből). A mentett oldalon `Címadatok - 1`, „Kötelező mező!” látszik; 14 oldalon a Házszám címke is hibásnak van jelölve, 10-en nincs mezőjelölés, a 16-os (Acsa) oldala nincs meg. **A hibás „Rögzítés kész” vázlatot hagy az OTR-ben** (a „Nyomtatás” gomb `ng-show="entity.id"` feltétele teljesül). A felhasználó ezeket kézzel javította.
- **2 tétel: az Excel régiója nincs a legördülőben**, mert az OTR a helyszínhez csak egy régiót kínál: 163 Balatonvilágos (Excel: Közép-Dunántúl, OTR: Dél-Dunántúl), 2360 Tiszaug (Excel: Dél-Alföld, OTR: Észak-Alföld). Vázlat nem készült. Az Excelt a felhasználó javítja.
- **Döntés:** a bot nem pótolja a címadatot, és nem keresi a vázlatokat. A felhasználó a naplót és az OTR azonosítókat kézzel írja át:
  `UPDATE items SET status = 'ok', otrid = '<OTR azonosító>', error = 'Kézzel javítva az OTR-ben' WHERE rowid = <rowid> AND round = 1;`
- **Új kapcsoló: `-r/--rows`** (pl. `-r 163,2360`), a `-b/-e`-vel együtt is érvényes. Csak szűr: az `ok` és az OTR azonosítós tételeket továbbra is kihagyja. **Buktató:** a `-r` nem nézi az OTR-t, ezért egy vázlatos tételhez új űrlapot kezd, és második vázlat vagy tétel keletkezhet. Ugyanez igaz a szűrő nélküli újrafuttatásra is, amíg a napló `failed`-et mutat.

### 8. Éles Döntés és Szerződés kör kész (2026-11-05 – 11-09)
- `data/be-tuzelo_2026.xlsx`, 2628 tétel: **mindhárom menetben 2628/2628 `ok`**, 2628 különböző OTR azonosító, a Döntés és a Szerződés menet azonosítói egyeznek.
- Átlagidő a napló szerint: Benyújtás 6,0 mp, Döntés 7,1 mp, Szerződés 4,9 mp/tétel (gépidő összesen ≈ 13,2 óra; a teljes 2628 tétel ≈ 18 mp/tétel).
- Döntés: 7 tétel az 1. próbálkozásra elhasalt (`dontes.tamkat_kategoria[0].idTamogatasiForma` select nem volt kezelhető), a 2. próbálkozás sikerült. 14 tételnél „<település> nevű önkormányzat nem található!”: az Excel településneve eltért az OTR-étől (pl. Sarud → Sarudi); a felhasználó javította az Excelt, és újrafuttatva (`otr_20261106_115225.log`, 14 tétel) mind `ok`.
- Szerződés: 2628 tétel, egyetlen hiba és újrapróbálkozás nélkül.

### 9. Robusztus találatkiválasztás a keresőben (2026-11-09)
- Ok: az OTR-ben az igénylő neve melléknévi alakú („Sarudi Községi Önkormányzat”, „Tahitótfalui Közös Önkormányzati Hivatal”), a régi `_findRow` szó szerinti egyezést várt, ezért 14 tétel „nem található” lett. Az Excel Helység oszlopának átírása („Sarudi”) nem kell; vissza lehet állítani a valódi névre, mindkettővel működik.
- `SupportListService._findRow`: a döntő az adószám első 8 jegye vagy az OTR azonosító + a státusz. A jelöltek közül az elsőt választja, amelynek a neve illik (`_nameMatches`: a település első szava egy név-szó eleje, legfeljebb 2 betű toldalékkal). Ha egyiké sem illik, de pontosan egy jelölt van, azt elfogadja WARNING-gal („az OTR-beli igénylő neve eltér”); több jelölt esetén `None`.
- Tesztek: `tests/test_support_list_service.py`. EDU-ban kipróbálva (`be-tuzelo-teszt_2026.xlsx`, rowid 1990–1995, Benyújtás + Döntés + Szerződés): 6/6 ok mindhárom menetben, a Sarud tételt („SARUDI KÖZSÉGI ÖNKORMÁNYZAT”) megtalálta, a tavalyi „Szerződött” tételeket a státusz kiszűrte, figyelmeztetés nem volt. A Szerződés első tételénél (a belépés utáni első keresés) a találati lista 20 mp alatt nem töltődött be („Empty search result grid”), az automatikus 2. próbálkozás sikerült; élesben 2628 Szerződésnél ilyen nem fordult elő.

## Mérés – EDU, 10 tétel (`data/be-tuzelo-teszt_2026.xlsx`)

| Menet | Eredmény | Idő/tétel |
|---|---|---|
| Benyújtás | 10/10 ok | 6,8 mp |
| Döntés | 10/10 ok | 7,8 mp |
| Szerződés | 10/10 ok | 4,3 mp |
| **Összesen** | | **≈ 19 mp** (korábban ~60 mp) |

2000 tétel ≈ 10,5 óra felügyelet nélkül. A maradék idő nagy része az OTR szerver válaszideje a „… kész” gombok után.

## Tudnivalók a környezetről
- Az EDU-ban csak a **KTM** támogató választható (`-sp KTM`); a VTM szövegét az élesben kell ellenőrizni.
- Git Bash-ben (`!` előtag) perjellel: `uv run python src/main.py ...`, nem `.\src\main.py`.
- A `.env`-ben `ENV=dev` = EDU, `ENV=prod` = éles.
- A `master` ág Seleniumot használ. Egy korábbi memória Playwright-migrációt és `newsite` ágat említ; ez a munkagépen nincs meg.

## A felhasználó döntései és preferenciái
- A **párhuzamos futtatást** (több böngésző/worker) a felhasználó **félretette**. Ne javasold magadtól. Technikailag lehetséges, mert az OTR engedi a több sessiont ugyanazzal a userrel.
- Az **OTR-es futásokat (EDU és éles) a felhasználó indítja** maga; Claude ne indítsa el őket, hanem adja meg a parancsot.
- A commit parancsot a felhasználó kéri kiírva; az ágat ő hozza létre.

## Nyitott teendők
1. Ellenőrizni az EDU-ban 1-2 tételnél, hogy a `setValue`-val beírt mezők (megnevezés, összefoglalás, cél) helyesen mentődtek-e.
2. A tűzifás betöltés (2628 tétel) élesben mindhárom menetben kész (2026-11-09).
3. Opcionális gyorsítások, EDU-ban kipróbálandók: `WebDriverConfig.PAGE_LOAD_STRATEGY = "eager"`, képek tiltása (`permissions.default.image`).
4. AlmaLinux szerveren EDU próbafutás (`-b 1 -e 5 --headless`, natívan vagy `scripts/otrbot-podman.sh run`-nal); az 1920×1080-as ablakkal is futtatni egy EDU kört, hogy ne romoljon el semmi.
5. A 4. menet (Lezárás) továbbra sincs megvalósítva.
6. Az IMPROVEMENT_PLAN.md fennmaradó pontjai.

## Fontos fájlok
- `src/otrbot/runner.py` – menetek, `_run_item`, `_recover`, `_fixingForm`, `_openExisting`
- `src/otrbot/journal.py` – napló, `eredmeny` nézet, `failed()`
- `src/otrbot/services/webdriver_service.py` – várakozások, strict mód, `setValue`, `readGrid`, `waitForPageIdle`, `StepTimings`
- `src/otrbot/services/support_list_service.py` – keresés OTR azonosító vagy kid + adószám alapján
- `src/otrbot/constants.py` – `TimeoutConfig`, `WebDriverConfig`, `RunnerConfig`
- Tesztek: `tests/test_journal.py`, `tests/test_runner_recovery.py`, `tests/test_support_list_service.py` (`uv run pytest`)
