from pathlib import Path


# ============================================================
# PROGRAM
# ============================================================

PROGRAM = "test"
TARGET = ""


# ============================================================
# OPTIONS
# ============================================================

ENABLE_POST_ANALYSIS = True


# ============================================================
# PATHS
# ============================================================

RESULTS_DIR = Path("results")

PROGRAM_DIR = RESULTS_DIR / PROGRAM

SEARCH_SOURCE_FILE = (
    PROGRAM_DIR / "search-engine-html-sources.json"
)

EXTRACTED_ASSETS_FILE = (
    PROGRAM_DIR / "search-extracted-assets.json"
)