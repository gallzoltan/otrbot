# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# Portable mode (after setup)
run.cmd -s "Benyújtás" -f "data.xlsx" -sp "BM"
```

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
- `-sp` / `--supporter`: Supporter organization - "BM" or "KTM"

### Optional Arguments
- `-b` / `--begin`: Starting row number (default: 4)
- `-e` / `--end`: Ending row number (default: 0, means all)

## Architecture

### Core Processing Flow (ModuleRunner)

The application follows a builder pattern for workflow configuration:

```python
runner = ModuleRunner(supporter="BM")
runner.load_datas(excel_file_path="data.xlsx", sheet_name='betolt') \
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
   - Validates and submits form with "RogzitesKesz" button

2. **Round 2 (Decision)**: Processes decisions on submitted applications
   - Searches for existing application by KID, council name, OTRID, status=1
   - Fills decision tab with deadlines and amounts
   - Updates decision categories
   - Submits with "DontesKesz" button

3. **Round 3 (Contract)**: Creates contracts for approved applications
   - Searches for existing application with status=2
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

- **TimeoutConfig** (src/otrbot/constants.py): WebDriver wait times (SHORT=10, DEFAULT=20, MEDIUM=50, LONG=100)
- **WebDriverConfig**: Firefox options for Selenium
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
1. `_validForm()`: Clicks validation button and checks for "nem talált hibát!" (no errors found)
2. `_fixingForm(action)`: Clicks fix/submit button (RogzitesKesz/DontesKesz/SzerzodesKesz) and checks for "sikeresen megtörtént" (successful)
3. Error logging with master.rowid and address.city for traceability

Note: Validation step is commented out in rounds 2 and 3, only fixingForm is used.

## Important Implementation Notes

### WebDriver Element Interaction

The WebDriver service (src/otrbot/services/webdriver_service.py) uses explicit waits for all interactions:
- Always wait for `presence_of_element_located`, then `visibility_of`, then `element_to_be_clickable`
- Use `selectBySendKeys` for autocomplete dropdowns (sends keys, waits for dropdown options, clicks first option)
- Use `selectOption` for standard select elements
- Grid navigation uses `findGridElementRows()` to locate table rows in the search results

### XPath Navigation Pattern

The OTR interface uses a tab-based navigation system. Always navigate to parent tab before child tabs:
```python
self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value)  # Parent first
self._navigateTab(main_tab=Navigate.TAB_MAIN_CLAIM.value, sub_tab=Navigate.TAB_SUB_CLAIM.value, index=0)  # Then child
```

### Error Handling

- All service methods return boolean success/failure
- Errors are logged with context: master.rowid (row identifier) and address.city (council name)
- The catchError method extracts error messages from the OTR interface's notice element

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
