"""
Page module for EPMC – wires layout + data together.
Mirrors the pattern in pages/pypi/pypi.py and pages/github/github.py.
"""

from app.layouts.epmc_layout import get_epmc_layout
from app.services.epmc_client import prepare_epmc_data

# ---- Prepare Data Once for Layout ----
entries_df, countries_df, authors_df, total_entries, citations = prepare_epmc_data()

layout = get_epmc_layout(entries_df, countries_df, authors_df, total_entries, citations)
