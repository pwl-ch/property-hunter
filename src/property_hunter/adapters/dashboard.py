"""Streamlit dashboard adapter."""

from pathlib import Path

import streamlit as st

from property_hunter.adapters.sqlite import SQLitePropertyRepository
from property_hunter.settings import get_settings


def run() -> None:
    """Render the local Streamlit dashboard."""
    settings = get_settings()
    repository = SQLitePropertyRepository(Path(settings.db_path))
    properties = repository.list(limit=500)

    st.set_page_config(page_title="PropertyHunter", layout="wide")
    st.title("PropertyHunter")
    st.dataframe(
        [
            {
                "title": item.listing.title,
                "price": item.extracted.price,
                "area_sqm": item.extracted.area_sqm,
                "parcel_id": item.extracted.parcel_id,
                "sync": item.sync_status.value,
            }
            for item in properties
        ],
        use_container_width=True,
    )

    selected_id = st.selectbox("Property", [item.id for item in properties])
    selected = next((item for item in properties if item.id == selected_id), None)
    if selected is None:
        return
    st.subheader(selected.listing.title)
    st.write(str(selected.listing.url))
    st.json(selected.model_dump(mode="json"))
