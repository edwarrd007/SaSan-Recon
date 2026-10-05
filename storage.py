import json
from datetime import datetime
from pathlib import Path


# ============================================================
# TIME
# ============================================================

def current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# LOAD ONE VALID JSON FILE
# ============================================================

def load_database(
    path: Path
) -> dict:

    if not path.exists():

        return {
            "data": {},
            "date": {},
        }

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            content = json.load(file)

        if not isinstance(
            content,
            dict
        ):
            return {
                "data": {},
                "date": {},
            }

        content.setdefault(
            "data",
            {}
        )

        content.setdefault(
            "date",
            {}
        )

        if not isinstance(
            content["data"],
            dict
        ):
            content["data"] = {}

        if not isinstance(
            content["date"],
            dict
        ):
            content["date"] = {}

        return content

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        print(
            "[!] Existing JSON is invalid."
        )

        print(
            "[*] Starting a new valid database."
        )

        return {
            "data": {},
            "date": {},
        }


# ============================================================
# SAVE PROGRAM DATA
# ============================================================

def save_program_data(
    path: Path,
    program: str,
    target: str,
    engines: dict
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load existing database
    # --------------------------------------------------------

    database = load_database(
        path
    )

    # --------------------------------------------------------
    # Update program object
    #
    # IMPORTANT:
    # We do NOT append raw JSON text.
    #
    # We update:
    #
    # data[program]
    #
    # --------------------------------------------------------

    database["data"][program] = {
        "target": target,
        "engines": engines,
    }

    # --------------------------------------------------------
    # Update date
    # --------------------------------------------------------

    database["date"][program] = (
        current_time()
    )

    # --------------------------------------------------------
    # Save ONE valid JSON object
    # --------------------------------------------------------

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            database,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# SAVE EXTRACTED ASSETS
# ============================================================

def save_extracted_assets(
    path: Path,
    program: str,
    target: str,
    raw_assets: dict,
    analyzed_assets: dict | None = None
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    database = load_database(
        path
    )

    program_data = {
        "target": target,
        "raw": raw_assets,
    }

    if analyzed_assets is not None:

        program_data["analysis"] = (
            analyzed_assets
        )

    database["data"][program] = (
        program_data
    )

    database["date"][program] = (
        current_time()
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            database,
            file,
            indent=4,
            ensure_ascii=False
        )