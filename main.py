import json
from pathlib import Path

from analyzer import AssetAnalyzer
from config import (
    ENABLE_POST_ANALYSIS,
    PROGRAM,
    TARGET,
)
from extractor import Extractor
from storage import save_extracted_assets


# ============================================================
# SOURCE FILE
# ============================================================

SOURCE_FILE = (
    Path("results")
    / PROGRAM
    / "search-engine-html-sources.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_source_file():

    if not SOURCE_FILE.exists():

        print(
            f"[ERROR] Source file not found:"
        )

        print(
            f"        {SOURCE_FILE}"
        )

        return None

    try:

        with open(
            SOURCE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except json.JSONDecodeError as exc:

        print(
            f"[ERROR] Invalid JSON:"
        )

        print(
            f"        {exc}"
        )

        return None

    if not isinstance(
        data,
        dict
    ):

        print(
            "[ERROR] Root JSON must be an object."
        )

        return None

    return data


# ============================================================
# MAIN EXTRACT
# ============================================================

def extract():

    print()
    print("=" * 70)

    print(
        f"Program : {PROGRAM}"
    )

    print(
        f"Target  : {TARGET}"
    )

    print(
        f"Source  : {SOURCE_FILE}"
    )

    print("=" * 70)

    database = load_source_file()

    if database is None:
        return

    # ========================================================
    # RAW ASSETS
    # ========================================================

    extracted_assets = {
        "URLs": [],
        "Domains": [],
        "IPv4": [],
        "Emails": [],
        "Hashes": [],
        "JWT-like": [],
        "Paths": [],
        "Security keyword lines": [],
    }

    # ========================================================
    # DATE-KEYED RECORDS
    #
    # {
    #     "2026...": {...},
    #     "2026...": {...}
    # }
    # ========================================================

    total_records = 0
    total_pages = 0

    for date_key, record in database.items():

        if not isinstance(
            record,
            dict
        ):
            continue

        record_program = record.get(
            "program",
            PROGRAM
        )

        # ----------------------------------------------------
        # Only process current program
        # ----------------------------------------------------

        if (
            record_program
            and record_program != PROGRAM
        ):
            continue

        engine_name = record.get(
            "engine",
            "unknown"
        )

        data = record.get(
            "data",
            {}
        )

        if not isinstance(
            data,
            dict
        ):
            continue

        pages = data.get(
            "pages",
            []
        )

        if not isinstance(
            pages,
            list
        ):
            continue

        total_records += 1

        print()
        print(
            f"[Record] {date_key}"
        )

        print(
            f"  Engine : {engine_name}"
        )

        print(
            f"  Pages  : {len(pages)}"
        )

        # ====================================================
        # PAGES
        # ====================================================

        for page_number, page in enumerate(
            pages,
            start=1
        ):

            if not isinstance(
                page,
                dict
            ):
                continue

            total_pages += 1

            html_source = page.get(
                "html_source",
                ""
            )

            # ------------------------------------------------
            # IMPORTANT
            #
            # dork.py stores page_source as STRING.
            # ------------------------------------------------

            if not isinstance(
                html_source,
                str
            ):

                print(
                    f"  [{engine_name}] "
                    f"page={page_number} "
                    f"SKIP: html_source type="
                    f"{type(html_source).__name__}"
                )

                continue

            if not html_source.strip():

                print(
                    f"  [{engine_name}] "
                    f"page={page_number} "
                    f"SKIP: empty html"
                )

                continue

            # ------------------------------------------------
            # EXTRACT
            # ------------------------------------------------

            extracted = Extractor.extract(
                text=html_source
            )

            # ------------------------------------------------
            # MERGE
            # ------------------------------------------------

            for category, values in (
                extracted.items()
            ):

                extracted_assets[
                    category
                ].extend(
                    values
                )

            print(
                f"  [{engine_name}] "
                f"page={page_number} "
                f"URLs={len(extracted['URLs'])} "
                f"Domains={len(extracted['Domains'])} "
                f"IPv4={len(extracted['IPv4'])} "
                f"Emails={len(extracted['Emails'])} "
                f"Hashes={len(extracted['Hashes'])} "
                f"JWT={len(extracted['JWT-like'])} "
                f"Paths={len(extracted['Paths'])}"
            )

    # ========================================================
    # DEDUPLICATE
    # ========================================================

    for category in extracted_assets:

        extracted_assets[category] = list(
            dict.fromkeys(
                extracted_assets[category]
            )
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)

    print(
        f"[+] Records processed : {total_records}"
    )

    print(
        f"[+] Pages processed   : {total_pages}"
    )

    print()

    for category, values in (
        extracted_assets.items()
    ):

        print(
            f"    {category:<28}"
            f"{len(values)}"
        )

    print("=" * 70)

    # ========================================================
    # ANALYSIS
    # ========================================================

    analyzed_assets = None

    if ENABLE_POST_ANALYSIS:

        print()
        print(
            "[*] Running AssetAnalyzer..."
        )

        analyzed_assets = (
            AssetAnalyzer.analyze(
                extracted_assets
            )
        )

        print(
            "[+] Analysis completed."
        )

    else:

        print()
        print(
            "[*] AssetAnalyzer disabled."
        )

    # ========================================================
    # SAVE
    # ========================================================

    output_file = (
        Path("results")
        / PROGRAM
        / "search-extracted-assets.json"
    )

    print()
    print(
        "[*] Saving extracted assets..."
    )

    save_extracted_assets(
        path=output_file,
        program=PROGRAM,
        target=TARGET,
        raw_assets=extracted_assets,
        analyzed_assets=analyzed_assets,
    )

    # ========================================================
    # DONE
    # ========================================================

    print()
    print("=" * 70)

    print(
        "[+] Extraction completed."
    )

    print(
        f"[+] Output: {output_file}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    extract()