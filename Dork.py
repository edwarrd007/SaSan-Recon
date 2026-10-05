import json
import os
import sys
import time

from datetime import datetime
from threading import Lock

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException


# =========================================================
# SaSaN-Recon
# =========================================================

APP_NAME = "SaSaN-Recon"

DORK_FILE = "dorks.json"

RESULTS_DIR = "results"

HTML_SOURCES_FILE = "search-engine-html-sources.json"

DEFAULT_WORKERS = 1
MAX_WORKERS = 1

print_lock = Lock()


# =========================================================
# Console
# =========================================================

def banner():

    print(r"""
 ███████╗ █████╗ ███████╗ █████╗ ███╗   ██╗
 ██╔════╝██╔══██╗██╔════╝██╔══██╗████╗  ██║
 ███████╗███████║███████╗███████║██╔██╗ ██║
 ╚════██║██╔══██║╚════██║╚════██║██║╚██╗██║
 ███████║██║  ██║███████║██║  ██║██║ ╚████║
 ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝

                 SaSaN-Recon
          Selenium Search Recon Tool

    """)


def log(message):

    with print_lock:
        print(message)


# =========================================================
# Time
# =========================================================

def current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )


# =========================================================
# Program Name
# =========================================================

def normalize_program_name(target):

    target = (
        target
        .replace("https://", "")
        .replace("http://", "")
        .strip("/")
        .strip()
        .lower()
    )

    if target.startswith("www."):
        target = target[4:]

    first_label = target.split(".")[0]

    return first_label


# =========================================================
# Configuration
# =========================================================

def load_config():

    if not os.path.exists(
        DORK_FILE
    ):

        print(
            f"[!] {DORK_FILE} was not found."
        )

        sys.exit(1)

    try:

        with open(
            DORK_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict
        ):

            print(
                "[!] dorks.json must contain "
                "a JSON object."
            )

            sys.exit(1)

        return data

    except json.JSONDecodeError as exc:

        print(
            f"[!] Invalid JSON: {exc}"
        )

        sys.exit(1)


# =========================================================
# Firefox
# =========================================================

def create_firefox(
    engine_name
):

    options = Options()

    options.page_load_strategy = "eager"

    options.set_preference(
        "browser.startup.page",
        0
    )

    options.set_preference(
        "browser.startup.homepage",
        "about:blank"
    )

    driver = webdriver.Firefox(
        options=options
    )

    driver.set_page_load_timeout(
        30
    )

    try:

        driver.maximize_window()

    except Exception:

        pass

    log(
        f"[+] Firefox Window created: "
        f"{engine_name}"
    )

    return driver


# =========================================================
# URL
# =========================================================

def build_url(
    base_url,
    dork,
    target
):

    query = dork.replace(
        "{target}",
        target
    )

    return base_url.format(
        query=query
    )


# =========================================================
# Manual TAB Accept
# =========================================================

def wait_for_tab_accept(
    engine_name,
    dork,
    tab_number
):

    print()
    print("=" * 72)

    print(
        f"[{engine_name}] New TAB requested"
    )

    print(
        f"Tab   : {tab_number}"
    )

    print(
        f"Dork  : {dork}"
    )

    print()

    print(
        "[ENTER] Accept and open this TAB"
    )

    print(
        "[S]     Skip this Dork"
    )

    print("=" * 72)

    while True:

        choice = input(
            "SaSaN-Recon > "
        ).strip().lower()

        if choice in (
            "",
            "enter",
            "e",
            "y",
            "yes"
        ):

            return True

        if choice in (
            "s",
            "skip",
            "n",
            "no"
        ):

            return False

        print(
            "[!] Press ENTER to accept "
            "or S to skip."
        )


# =========================================================
# Extract Links
# =========================================================

def extract_links(
    driver
):

    links = set()

    try:

        elements = driver.find_elements(
            By.TAG_NAME,
            "a"
        )

        for element in elements:

            try:

                href = element.get_attribute(
                    "href"
                )

                if not href:
                    continue

                if href.startswith(
                    "http://"
                ):

                    links.add(
                        href
                    )

                elif href.startswith(
                    "https://"
                ):

                    links.add(
                        href
                    )

            except WebDriverException:

                continue

    except WebDriverException:

        pass

    return sorted(
        links
    )


# =========================================================
# Open Dork TAB
# =========================================================

def open_dork_tab(
    driver,
    engine_name,
    dork,
    url,
    tab_number
):

    accepted = wait_for_tab_accept(
        engine_name,
        dork,
        tab_number
    )

    if not accepted:

        log(
            f"[{engine_name}][Tab {tab_number}] "
            f"SKIPPED BY USER"
        )

        return {
            "handle": None,
            "tab_number": tab_number,
            "dork": dork,
            "requested_url": url,
            "url": None,
            "links": [],
            "link_count": 0,
            "status": "skipped"
        }

    try:

        # -------------------------------------------------
        # First dork uses original tab
        # -------------------------------------------------

        if tab_number == 1:

            handle = (
                driver.current_window_handle
            )

        # -------------------------------------------------
        # Other dorks use new tabs
        # -------------------------------------------------

        else:

            driver.switch_to.new_window(
                "tab"
            )

            handle = (
                driver.current_window_handle
            )

        log(
            f"[{engine_name}][Tab {tab_number}] "
            f"Opening:"
        )

        log(
            f"    {url}"
        )

        driver.get(
            url
        )

        time.sleep(1)

        current_url = (
            driver.current_url
        )

        log(
            f"[{engine_name}][Tab {tab_number}] "
            f"Loaded:"
        )

        log(
            f"    {current_url}"
        )

        return {
            "handle": handle,
            "tab_number": tab_number,
            "dork": dork,
            "requested_url": url,
            "url": current_url,
            "links": [],
            "link_count": 0,
            "status": "ready"
        }

    except Exception as exc:

        log(
            f"[{engine_name}][Tab {tab_number}] "
            f"ERROR: {exc}"
        )

        return {
            "handle": None,
            "tab_number": tab_number,
            "dork": dork,
            "requested_url": url,
            "url": None,
            "links": [],
            "link_count": 0,
            "status": "error",
            "error": str(exc)
        }


# =========================================================
# Process One TAB
# =========================================================

def process_tab(
    driver,
    engine_name,
    tab
):

    handle = tab.get(
        "handle"
    )

    if not handle:
        return tab

    try:

        driver.switch_to.window(
            handle
        )

        log(
            f"[{engine_name}][Tab "
            f"{tab['tab_number']}] "
            f"Processing..."
        )

        links = extract_links(
            driver
        )

        tab["url"] = (
            driver.current_url
        )

        tab["links"] = links

        tab["link_count"] = (
            len(links)
        )

        tab["status"] = "completed"

        log(
            f"[{engine_name}]"
            f"[Tab {tab['tab_number']}] "
            f"Found {len(links)} links"
        )

        return tab

    except Exception as exc:

        log(
            f"[{engine_name}]"
            f"[Tab {tab['tab_number']}] "
            f"Extraction error: {exc}"
        )

        tab["status"] = "error"

        tab["error"] = str(
            exc
        )

        return tab


# =========================================================
# HTML Source Extraction
# =========================================================

def extract_html_source(
    driver,
    engine_name,
    tab
):

    handle = tab.get(
        "handle"
    )

    if not handle:

        return {
            "engine": engine_name,
            "tab_number": tab.get(
                "tab_number"
            ),
            "dork": tab.get(
                "dork"
            ),
            "requested_url": tab.get(
                "requested_url"
            ),
            "url": tab.get(
                "url"
            ),
            "status": tab.get(
                "status"
            ),
            "html_source": None,
            "html_length": 0,
            "error": "No valid browser handle"
        }

    try:

        driver.switch_to.window(
            handle
        )

        current_url = (
            driver.current_url
        )

        # IMPORTANT:
        # page_source must remain a STRING.
        html_source = (
            driver.page_source or ""
        )

        title = ""

        try:

            title = (
                driver.title or ""
            )

        except Exception:

            pass

        result = {
            "engine": engine_name,
            "tab_number": tab.get(
                "tab_number"
            ),
            "dork": tab.get(
                "dork"
            ),
            "requested_url": tab.get(
                "requested_url"
            ),
            "url": current_url,
            "title": title,
            "status": "source_saved",
            "html_length": len(
                html_source
            ),
            "html_source": html_source
        }

        log(
            f"[{engine_name}]"
            f"[Tab {tab['tab_number']}] "
            f"HTML source captured "
            f"({len(html_source)} bytes)"
        )

        return result

    except Exception as exc:

        log(
            f"[{engine_name}]"
            f"[Tab {tab.get('tab_number')}] "
            f"HTML source error: {exc}"
        )

        return {
            "engine": engine_name,
            "tab_number": tab.get(
                "tab_number"
            ),
            "dork": tab.get(
                "dork"
            ),
            "requested_url": tab.get(
                "requested_url"
            ),
            "url": tab.get(
                "url"
            ),
            "status": "source_error",
            "html_source": None,
            "html_length": 0,
            "error": str(exc)
        }


# =========================================================
# Load JSON Database
# =========================================================

def load_json_database(
    output_file
):

    if not os.path.exists(
        output_file
    ):
        return {}

    try:

        with open(
            output_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            dict
        ):

            return data

        return {}

    except (
        json.JSONDecodeError,
        OSError
    ):

        print(
            "[!] Existing JSON is invalid."
        )

        print(
            "[*] Starting with a new JSON object."
        )

        return {}


# =========================================================
# Append One Date-Keyed Record
# =========================================================

def append_json_record(
    output_file,
    record
):

    os.makedirs(
        os.path.dirname(
            output_file
        ),
        exist_ok=True
    )

    # -----------------------------------------------------
    # Load existing JSON
    # -----------------------------------------------------

    database = load_json_database(
        output_file
    )

    # -----------------------------------------------------
    # Generate unique DATE key
    # -----------------------------------------------------

    date_key = current_time()

    while date_key in database:

        time.sleep(
            0.000001
        )

        date_key = current_time()

    # -----------------------------------------------------
    # DATE IS THE ROOT KEY
    # -----------------------------------------------------

    database[date_key] = record

    # -----------------------------------------------------
    # Rewrite valid JSON
    #
    # NEVER use "a".
    # -----------------------------------------------------

    temp_file = (
        f"{output_file}.tmp"
    )

    try:

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                database,
                file,
                indent=4,
                ensure_ascii=False
            )

        # Atomic-ish replacement.
        os.replace(
            temp_file,
            output_file
        )

    except Exception:

        try:

            if os.path.exists(
                temp_file
            ):
                os.remove(
                    temp_file
                )

        except OSError:

            pass

        raise

    return date_key


# =========================================================
# Save HTML Sources
# =========================================================

def save_html_sources(
    program,
    target,
    engine_name,
    html_sources
):

    # -----------------------------------------------------
    # Program folder
    # -----------------------------------------------------

    program_dir = os.path.join(
        RESULTS_DIR,
        program
    )

    os.makedirs(
        program_dir,
        exist_ok=True
    )

    output_file = os.path.join(
        program_dir,
        HTML_SOURCES_FILE
    )

    # -----------------------------------------------------
    # DATE -> DATA
    # -----------------------------------------------------

    record = {

        "application": APP_NAME,

        "program": program,

        "target": target,

        "engine": engine_name,

        "data": {

            "pages": html_sources,

            "page_count": len(
                html_sources
            )
        }
    }

    date_key = append_json_record(
        output_file,
        record
    )

    print()

    log(
        "[+] HTML sources saved:"
    )

    log(
        f"    {output_file}"
    )

    log(
        f"[+] Date: {date_key}"
    )

    log(
        f"[+] Program: {program}"
    )

    log(
        f"[+] Engine: {engine_name}"
    )

    log(
        f"[+] Pages: {len(html_sources)}"
    )


# =========================================================
# Save Normal Search Engine Results
# =========================================================

def save_results(
    program,
    engine_name,
    target,
    tabs
):

    # -----------------------------------------------------
    # Engine-specific directory
    # -----------------------------------------------------

    output_dir = os.path.join(
        RESULTS_DIR,
        program,
        engine_name
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    safe_target = (
        target
        .replace(
            "/",
            "_"
        )
        .replace(
            "\\",
            "_"
        )
        .replace(
            ":",
            "_"
        )
    )

    output_file = os.path.join(
        output_dir,
        f"{safe_target}.json"
    )

    # -----------------------------------------------------
    # Unique links
    # -----------------------------------------------------

    unique_links = set()

    for tab in tabs:

        for link in tab.get(
            "links",
            []
        ):

            unique_links.add(
                link
            )

    # -----------------------------------------------------
    # Record
    # -----------------------------------------------------

    record = {

        "application": APP_NAME,

        "program": program,

        "engine": engine_name,

        "target": target,

        "data": {

            "tabs": tabs,

            "unique_links": sorted(
                unique_links
            ),

            "statistics": {

                "tabs": len(
                    tabs
                ),

                "unique_links": len(
                    unique_links
                )
            }
        }
    }

    # -----------------------------------------------------
    # DATE KEY
    # -----------------------------------------------------

    date_key = append_json_record(
        output_file,
        record
    )

    print()

    print(
        "[+] Results saved:"
    )

    print(
        f"    {output_file}"
    )

    print(
        f"[+] Date: {date_key}"
    )

    print(
        f"[+] Unique links: "
        f"{len(unique_links)}"
    )


# =========================================================
# Run One Search Engine
# =========================================================

def run_engine(
    engine_name,
    target,
    program,
    config
):

    engine_config = config.get(
        engine_name,
        {}
    )

    if not isinstance(
        engine_config,
        dict
    ):

        return None

    if not engine_config.get(
        "enabled",
        False
    ):

        log(
            f"[{engine_name}] "
            f"Disabled."
        )

        return None

    # -----------------------------------------------------
    # Base URL
    # -----------------------------------------------------

    base_url = engine_config.get(
        "base_url"
    )

    if not base_url:

        log(
            f"[{engine_name}] ERROR: "
            f"base_url is missing in dorks.json"
        )

        return None

    # -----------------------------------------------------
    # Dorks
    # -----------------------------------------------------

    dorks = engine_config.get(
        "dorks",
        []
    )

    if not isinstance(
        dorks,
        list
    ):

        log(
            f"[{engine_name}] ERROR: "
            f"dorks must be a list."
        )

        return None

    if not dorks:

        log(
            f"[{engine_name}] "
            f"No dorks configured."
        )

        return None

    driver = None

    try:

        print()
        print()
        print(
            "=" * 72
        )

        print(
            f"[+] STARTING SEARCH ENGINE: "
            f"{engine_name.upper()}"
        )

        print(
            f"[+] Program: {program}"
        )

        print(
            f"[+] Target: {target}"
        )

        print(
            f"[+] Dorks: {len(dorks)}"
        )

        print(
            "=" * 72
        )

        # -------------------------------------------------
        # One Firefox Window
        # -------------------------------------------------

        driver = create_firefox(
            engine_name
        )

        tabs = []

        # -------------------------------------------------
        # Open all dorks
        # -------------------------------------------------

        for tab_number, dork in enumerate(
            dorks,
            start=1
        ):

            url = build_url(
                base_url,
                dork,
                target
            )

            tab = open_dork_tab(
                driver,
                engine_name,
                dork,
                url,
                tab_number
            )

            tabs.append(
                tab
            )

        # -------------------------------------------------
        # Process tabs
        # -------------------------------------------------

        print()
        print(
            "-" * 72
        )

        print(
            f"[{engine_name}] "
            f"All Dork tabs are ready."
        )

        print(
            f"[{engine_name}] "
            f"Starting TAB-by-TAB extraction."
        )

        print(
            "-" * 72
        )

        for index, tab in enumerate(
            tabs
        ):

            tabs[index] = process_tab(
                driver,
                engine_name,
                tab
            )

        # -------------------------------------------------
        # Save normal results
        # -------------------------------------------------

        save_results(
            program,
            engine_name,
            target,
            tabs
        )

        # -------------------------------------------------
        # HTML Sources
        # -------------------------------------------------

        print()
        print(
            "-" * 72
        )

        print(
            f"[{engine_name}] "
            f"Starting HTML source collection."
        )

        print(
            "-" * 72
        )

        html_sources = []

        for tab in tabs:

            source_data = extract_html_source(
                driver,
                engine_name,
                tab
            )

            html_sources.append(
                source_data
            )

        # -------------------------------------------------
        # Save HTML source data
        # -------------------------------------------------

        save_html_sources(
            program,
            target,
            engine_name,
            html_sources
        )

        # -------------------------------------------------
        # Complete
        # -------------------------------------------------

        print()
        print(
            "=" * 72
        )

        print(
            f"[+] {engine_name.upper()} "
            f"RECON COMPLETED."
        )

        print(
            f"[+] Dorks processed: "
            f"{len(tabs)}"
        )

        print(
            f"[+] HTML sources saved: "
            f"{len(html_sources)}"
        )

        print(
            f"[+] {engine_name.upper()} "
            f"Firefox Window remains OPEN."
        )

        print(
            "=" * 72
        )

        return driver

    except Exception as exc:

        log(
            f"[{engine_name}] Fatal error: "
            f"{exc}"
        )

        return driver


# =========================================================
# Run Recon Sequentially
# =========================================================

def run_recon(
    target,
    program,
    config
):

    enabled_engines = []

    # -----------------------------------------------------
    # Preserve dorks.json order
    # -----------------------------------------------------

    for engine_name, engine_config in (
        config.items()
    ):

        if not isinstance(
            engine_config,
            dict
        ):

            continue

        if engine_config.get(
            "enabled",
            False
        ):

            enabled_engines.append(
                engine_name
            )

    if not enabled_engines:

        print(
            "[!] No search engine is enabled."
        )

        return []

    print()
    print(
        "=" * 72
    )

    print(
        "Enabled engines:"
    )

    for index, engine in enumerate(
        enabled_engines,
        start=1
    ):

        print(
            f"    [{index}] {engine}"
        )

    print()

    print(
        "[+] Execution mode: SEQUENTIAL"
    )

    print(
        "[+] One Search Engine at a time."
    )

    print(
        "=" * 72
    )

    drivers = []

    # -----------------------------------------------------
    # Sequential execution
    # -----------------------------------------------------

    for engine_name in enabled_engines:

        print()
        print(
            "#" * 72
        )

        print(
            f"# NEXT ENGINE: "
            f"{engine_name.upper()}"
        )

        print(
            "#" * 72
        )

        driver = run_engine(
            engine_name,
            target,
            program,
            config
        )

        if driver:

            drivers.append(
                (
                    engine_name,
                    driver
                )
            )

        print()

        print(
            f"[+] {engine_name.upper()} "
            f"finished."
        )

    return drivers


# =========================================================
# CLI
# =========================================================

def main():

    banner()

    config = load_config()

    print(
        "[1] Run Google"
    )

    print(
        "[2] Run All Enabled Engines Sequentially"
    )

    print(
        "[3] Exit"
    )

    print()

    choice = input(
        "SaSaN-Recon > "
    ).strip()

    if choice == "3":

        print(
            "[+] Bye."
        )

        return

    if choice not in (
        "1",
        "2"
    ):

        print(
            "[!] Invalid option."
        )

        return

    print()

    target = input(
        "Target domain > "
    ).strip()

    if not target:

        print(
            "[!] Target cannot be empty."
        )

        return

    # -----------------------------------------------------
    # Normalize target
    # -----------------------------------------------------

    target = (
        target
        .replace(
            "https://",
            ""
        )
        .replace(
            "http://",
            ""
        )
        .strip("/")
    )

    # -----------------------------------------------------
    # Program name
    # -----------------------------------------------------

    program = normalize_program_name(
        target
    )

    print()
    print(
        f"[+] Program: {program}"
    )

    print(
        f"[+] Target : {target}"
    )

    print()

    # -----------------------------------------------------
    # Google only
    # -----------------------------------------------------

    if choice == "1":

        google_only_config = {

            "google": config.get(
                "google",
                {}
            )
        }

        run_recon(
            target,
            program,
            google_only_config
        )

    # -----------------------------------------------------
    # All enabled engines
    # -----------------------------------------------------

    elif choice == "2":

        run_recon(
            target,
            program,
            config
        )

    # -----------------------------------------------------
    # Browsers remain open
    # -----------------------------------------------------

    print()
    print(
        "=" * 72
    )

    print(
        "[+] Recon completed."
    )

    print(
        "[+] Browser Window(s) are still open."
    )

    print(
        "[+] SaSaN-Recon does NOT close them."
    )

    print(
        "[+] Close them manually when finished."
    )

    print(
        "=" * 72
    )

    # -----------------------------------------------------
    # Keep process alive
    # -----------------------------------------------------

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        print()

        print(
            "[!] SaSaN-Recon stopped."
        )

        print(
            "[!] Browser windows were NOT "
            "closed by the program."
        )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    main()