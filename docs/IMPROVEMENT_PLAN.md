# OTR Bot Kod Atvizsgalas - Javitasi Terv

## Osszefoglalo

A kodbazis atvizsgalasa soran **85+ problemat** azonositottam. Ez a terv a legfontosabb javitasokat tartalmazza prioritas szerint rendezve.

---

## 1. KRITIKUS HIBAK (Azonnal javitando)

### 1.1 NoneType crash a support_list_service.py-ban
- **Fajl:** `src/otrbot/services/support_list_service.py:46-54`
- **Problema:** `findGridElementRows()` visszaadhat `None`-t, de nincs ellenorzes a `for` ciklus elott
- **Javitas:** None-check hozzaadasa

### 1.2 catchError() None visszateresi ertek kezeletlen
- **Fajl:** `src/otrbot/runner.py:134, 144, 154`
- **Problema:** `catchError()` visszaadhat `None`-t, de a string muveletek crashelnek
- **Javitas:** `if result and "..." in result:` minta hasznalata

### 1.3 IndexError kockazat kategoria feldolgozasnal
- **Fajl:** `src/otrbot/services/submission_service.py:149-157`, `decision_service.py:100-110`
- **Problema:** Max 6 kategoria van hardkodolva, de nincs ellenorzes
- **Javitas:** Bounds checking hozzaadasa

### 1.4 SupportSearchTable IndexError
- **Fajl:** `src/otrbot/models/search_table.py:2-10`
- **Problema:** `collist` hossza nincs ellenorizve index hozzaferes elott
- **Javitas:** Length validation hozzaadasa

---

## 2. FONTOS JAVITASOK

### 2.1 Kornyezeti valtozok validalasa
- **Fajl:** `src/otrbot/config.py:19-25`
- **Problema:** Hianyzo env valtozok `None` erteket adnak, ami kesobb erthetetlen hibat okoz
- **Javitas:** Explicit validacio es `EnvironmentError` dobasa

### 2.2 WebDriver resource leak
- **Fajl:** `src/otrbot/runner.py`
- **Problema:** Nincs automatikus cleanup exception eseten; bongeszo nyitva maradhat
- **Javitas:** Context manager pattern vagy try-finally hasznalata

### 2.3 Silent data loss zip()-nel
- **Fajl:** `src/otrbot/runner.py:46, 70, 97`
- **Problema:** Ha a Stack listai kulonbozo hosszuak, adatok elvesznek csendben
- **Javitas:** `zip_longest` vagy hossz-validacio

### 2.4 JavaScript injection kockazat
- **Fajl:** `src/otrbot/services/webdriver_service.py:115`
- **Problema:** String interpolacio JavaScript-ben: `f"return document.getElementById('{item_id}').checked"`
- **Javitas:** Parameterezett execute_script() hasznalata

---

## 3. KOD DUPLIKACIO (Refaktoralas)

### 3.1 `__split_by_dots()` metodus
- **Fajlok:** `submission_service.py:159-164`, `decision_service.py:112-117`
- **Javitas:** Kiemeles utility modulba

### 3.2 Kategoria feldolgozo ciklus
- **Fajlok:** `submission_service.py:147-157`, `decision_service.py:100-110`
- **Javitas:** Kozos base service vagy utility fuggveny

### 3.3 Round metodusok (runner.py)
- **Fajl:** `src/otrbot/runner.py:44-119`
- **Problema:** `_run_round1`, `_run_round2`, `_run_round3` nagyon hasonlo strukturaju
- **Javitas:** Template method pattern

### 3.4 Logger inicializalas
- **Fajlok:** Minden service fajl
- **Problema:** `logging.getLogger()` nev nelkul, helyett `logging.getLogger(__name__)` kellene
- **Javitas:** Egyseges logger hasznalat az `otr_logging` modulbol

---

## 4. TIPUSBIZTONSAG ES VALIDACIO

### 4.1 Penzugyi mezok string helyett Decimal
- **Fajl:** `src/otrbot/models/amount.py`
- **Problema:** `claim_sum`, `decision_awarded_sum` stb. mind `str` tipusu
- **Javitas:** `Decimal` vagy `float` tipus + validacio

### 4.2 Datum mezok string helyett date
- **Fajl:** `src/otrbot/models/deadline.py`
- **Problema:** Minden datum `str` tipusu
- **Javitas:** `datetime.date` tipus + formatum validacio

### 4.3 Hianyzo validacio pandas feldolgozasnal
- **Fajl:** `src/otrbot/services/pandas_service.py:30-31`
- **Problema:** `fillna('')` utan nincs ellenorzes kotelezo mezokre
- **Javitas:** Validacio hozzaadasa

### 4.4 SupportSearchTable typo
- **Fajl:** `src/otrbot/models/search_table.py:9`
- **Problema:** `constuct_name` helyett `construct_name`

---

## 5. KOD TISZTITAS

### 5.1 Kommentezett kod eltavolitasa
- **Fajlok:** `runner.py:59-66, 84-91, 109-116`, `webdriver_service.py:6, 26-28, 51, 93-94`, `main.py:24-42`

### 5.2 Unused imports eltavolitasa
- **Fajl:** `webdriver_service.py:15` - `ElementClickInterceptedException` nincs hasznalva

### 5.3 Konstans elnevezes typo
- **Fajl:** `decision_service.py:43` - `SEARCH_DECISION_COLSE` -> `SEARCH_DECISION_CLOSE`

### 5.4 Hardkodolt sleep ertekek
- **Fajl:** `runner.py:76, 103` - `time.sleep(2)` helyett konfiguralhat timeout

---

## 6. HIANYZO FUNKCIO

### 6.1 Round 4 (Lezaras) nincs implementalva
- **Fajl:** `src/otrbot/runner.py:13-17`
- **Problema:** Dokumentacio emliti, de a kodban nincs `_run_round4()`

---

## Javasolt Vegrehajtasi Sorrend

1. **Fazis 1:** Kritikus hibak javitasa (1.1-1.4)
2. **Fazis 2:** Fontos javitasok (2.1-2.4)
3. **Fazis 3:** Kod duplikacio csokkentese (3.1-3.4)
4. **Fazis 4:** Tipusbiztonsag javitasa (4.1-4.4)
5. **Fazis 5:** Kod tisztitas (5.1-5.4)

---

## Teszteles

- Minden modositas utan: `pytest` futtatas
- Manualis teszt: `python src/main.py -s "Benyujtas" -f "test.xlsx" -sp "BM"` dev kornyezetben
