# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Current state of work, decisions and open tasks: read `docs/MEMO.md` at the start of a session and update it at the end.**

## Project Overview

OTR Bot is a Selenium-based automation tool for the Hungarian OTR (Országos Támogatás–ellenőrzési Rendszer) government subsidy management system. It automates the submission, decision, contract, and closing processes for municipal subsidy applications.

## Build and Development Commands

### Environment Setup
```bash
# Create .env file from example
cp src/.env.example src/.env

# Set required environment variables:
# - ENV: 'dev' (uses OTR_EDU_*) or 'prod' (uses OTR_*)
# - SYSTEM: 'windows' or 'linux'
# - OTR_URL, OTR_USERNAME, OTR_PASSWORD (production)
# - OTR_EDU_URL, OTR_EDU_USERNAME, OTR_EDU_PASSWORD (education/testing)
```

### Build and Package
```bash
# Build the project (creates wheel in dist/)
uv build

# For portable Windows deployment
uv build
mkdir otrbot-portable\whl
copy dist\otrbot-0.1.0-py3-none-any.whl otrbot-portable\whl\
# Then download Python embeddable package to otrbot-portable\python\
# Run install.cmd in otrbot-portable directory
```

### Running the Application
```bash
# Direct execution
python src/main.py -s "Benyújtás" -f "data.xlsx" -sp "BM"

# Unattended, without a browser window, only rowid 1..20
python src/main.py -s "Benyújtás" -f "data.xlsx" -sp "VTM" -b 1 -e 20 --headless

# Portable mode (after setup)
run.cmd -s "Benyújtás" -f "data.xlsx" -sp "BM"
```

From Git Bash (e.g. the `!` prefix in Claude Code) use forward slashes in paths: `src/main.py`, not `.\src\main.py`.

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_decision_service.py
```

### Required Arguments
- `-s` / `--status`: Process stage - "Benyújtás" (submission), "Döntés" (decision), "Szerződés" (contract), "Lezárás" (closing)
- `-f` / `--file`: Excel file path (*.xlsx)
- `-sp` / `--supporter`: Supporter organization - "BM", "KTM" or "VTM" (the EDU environment only offers KTM)

### Optional Arguments
- `-b` / `--begin`: First `rowid` to process (filters on the Excel `rowid` column, not the Excel row number; default: first row)
- `-e` / `--end`: Last `rowid` to process (default: 0, means all)
- `--headless`: Run Firefox without a window

### Unattended Run: Journal, Resume, Results

- **Journal**: every (rowid, round) outcome is stored in `<excel>.journal.sqlite` next to the Excel file (src/otrbot/journal.py). Statuses: `ok`, `failed`, `pending`.
- **Resume**: rerunning the same command skips items that are already `ok` in that round; `failed`/`pending` items are processed again. Delete the journal file to start from scratch.
- **Results**: after every run `<excel>_eredmeny.xlsx` is written: the input rows plus `otr_azonosito` and per-round `<round>_status`, `<round>_probalkozas`, `<round>_hiba` columns.
- **Logs**: one file per run, `logs/otr_<timestamp>.log`; the end of the log lists the 10 slowest browser steps. Screenshot + HTML of every failed attempt: `logs/fail/<rowid>_r<round>_a<attempt>.png/.html`.
- Exit code is non-zero if any item failed.

## Architecture

### Core Processing Flow (ModuleRunner)

The application follows a builder pattern for workflow configuration:

```python
runner = ModuleRunner(supporter="BM", journal=Journal.for_excel("data.xlsx"))
runner.load_datas(excel_file_path="data.xlsx", sheet_name='betolt', begin=1, end=0) \
    .start_driver(options=get_driver_options(), system="windows", headless=False) \
    .login_otr(url=config.url, username=config.username, password=config.password) \
    .run(round=1)  # 1=submission, 2=decision, 3=contract, 4=closing
```

### Round-Based Processing

The system processes subsidies in sequential rounds (src/otrbot/runner.py):

1. **Round 1 (Submission)**: Creates new subsidy applications
   - Navigates to "New Support" menu
   - Fills claiming party basic info (Igénylő alapadatok)
   - Fills claim basic data, place of use, and support categories
   - Submits form with "RogzitesKesz" button (the OTR id is not shown afterwards; round 2 captures it)

2. **Round 2 (Decision)**: Processes decisions on submitted applications
   - Searches by OTR id if known (journal, then Excel `otrid`); otherwise by KID + tax number (`regid`)
   - Picks the grid row by council name, status ("Benyújtott") and tax number prefix
   - Saves the OTR id from the grid's first column to the journal (it is not shown after submission)
   - Fills decision tab with deadlines and amounts
   - Updates decision categories
   - Submits with "DontesKesz" button

3. **Round 3 (Contract)**: Creates contracts for approved applications
   - Searches by the OTR id captured in round 2 (or Excel `otrid`), status=2
   - Fills contract tab with deadlines
   - Submits with "SzerzodesKesz" button

### Service Layer Architecture

All form-filling services use context managers (`with` statements) and follow a common pattern:

- **LoginService**: Handles OTR authentication
- **SubmissionService**: Round 1 form filling (claiming party + claim details)
- **DecisionService**: Round 2 form filling (decision details)
- **ContractService**: Round 3 form filling (contract details)
- **SupportListService**: Search and navigation within existing applications
- **WebDriverService**: Low-level Selenium wrapper with robust element interaction

### Data Models (src/otrbot/models/)

Excel data is parsed into typed dataclasses via pandas_service.py:

- **Master**: Core subsidy info (rowid, kid, regid, otrid, aht, category, activity, form)
- **Address**: Location data (postal_code, city, street, house_number, region)
- **Denomination**: Claim descriptions (claim_name, claim_source_name, claim_summary, claim_goal)
- **Deadline**: All date fields (submission, decision, support period, contract)
- **Amount**: All financial fields (claim amounts, decision costs, awarded sums)
- **Stack**: Container holding lists of all above models, zipped together during processing

### Constants and Configuration

- **TimeoutConfig** (src/otrbot/constants.py): WebDriver wait times (SHORT=10, DEFAULT=20, MEDIUM=50, LONG=100) and polling interval (POLL=0.05)
- **WebDriverConfig**: Firefox options and preferences, `PAGE_LOAD_STRATEGY`, `DISABLE_ANIMATIONS`
- **RunnerConfig**: `MAX_ATTEMPTS` per item (2), `MAX_CONSECUTIVE_FAILURES` before the run stops (10), `FAIL_DIR`
- **Navigate**: XPath constants for all main/sub tabs in OTR interface
- **SubmitForms**: XPath constants for form action buttons (validation, save, submit)
- **Categories**: State aid category mappings (de minimis, public service compensation, etc.)

### Excel Input Format

The input Excel file must have a sheet named 'betolt' with these columns (row 1 is skipped as header):
- kid, regid, otrid, aht, form, category (Master data)
- postal_code, city, street, house_number, region (Address data)
- claim_name, claim_source_name, claim_summary, claim_goal (Denomination)
- claim_submission_date, decision_date, decision_support_begin, decision_support_finish, contract_entry_date (Deadlines)
- claim_sum, claim_sum_content, decision_all_cost, decision_cost, decision_awarded_sum, decision_own_source, decision_other_sum, decision_sum_content (Amounts)

### Form Validation and Submission Pattern

All rounds follow a three-step submission pattern in runner.py:
1. `_validForm()`: Clicks validation button and checks for "nem talált hibát!" (no errors found) - currently unused
2. `_fixingForm(action)`: Clicks fix/submit button (RogzitesKesz/DontesKesz/SzerzodesKesz), confirms, and requires "sikeresen megtörtént"
3. Error logging with master.rowid and address.city for traceability

A failure after the confirmation raises `FinalSubmitError` (`SubmittedUncertain` if no message appeared). These are never retried, because a retry could create a duplicate; the journal error starts with "BIZONYTALAN" when the item must be checked manually in OTR.

## Important Implementation Notes

### WebDriver Element Interaction

The WebDriver service (src/otrbot/services/webdriver_service.py) uses explicit waits for all interactions:
- One wait per interaction (`element_to_be_clickable` / `visibility_of_element_located`) via `_wait()`, polling every 0.05 s
- `clickElement` retries while an overlay intercepts the click
- Use `sendKeys` for dates, amounts and fields that need key events; `setValue` (JS native setter + events) for long plain text
- Use `selectBySendKeys` for autocomplete dropdowns (sends keys, waits for dropdown options, clicks first option)
- Use `selectOption` for standard select elements; it waits until the requested option is loaded
- `readGrid()` reads the search result grid with one JS call and waits for its rows
- `waitForPageIdle()` waits until no AngularJS `$http` request is pending. The app is bootstrapped on `#otr_angular_inner` (not `body`); `_navigateTab` calls it after every tab click, otherwise async loads overwrite fields filled too early (seen on the Decision tab)
- Every interaction is timed (`StepTimings`), logged at DEBUG and summarized at the end of the run

### XPath Navigation Pattern

The OTR interface uses a tab-based navigation system. Always navigate to parent tab before child tabs:
```python
self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value)  # Parent first
self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value, sub_tab=Navigate.TAB_SUB_CLAIM.value, index=0)  # Then child
```

### Error Handling

- The runner sets `WebDriver.strict = True`: a failed interaction raises `StepFailed` instead of returning False, so the item is abandoned immediately (fail-fast)
- `ModuleRunner._run_item` retries an item up to `MAX_ATTEMPTS`; between attempts `_recover` saves debug info, reloads the start URL, logs in again if needed, and restarts Firefox if it died
- Errors are logged with context: master.rowid (row identifier) and address.city (council name)
- The catchError method extracts error messages from the OTR interface's notice element (returns "" if none)

### Config Management

Config.from_env() switches between dev/prod environments:
- ENV='dev' uses OTR_EDU_* credentials for testing
- ENV='prod' uses OTR_* credentials for production
- SYSTEM setting determines WebDriver initialization (windows vs linux)

## Dependencies

- Python 3.12.10+
- Selenium 4.33.0+ with Firefox (geckodriver)
- pandas + openpyxl for Excel parsing
- python-dotenv for environment configuration
- unidecode for text normalization

## Portable Deployment

For Windows deployment without Python installation:
1. Build wheel with `uv build`
2. Copy wheel to `otrbot-portable/whl/`
3. Download Python embeddable package to `otrbot-portable/python/`
4. Run `install.cmd` (sets up pip, installs dependencies)
5. Use `run.cmd` with standard arguments
