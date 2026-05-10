"""CSV and KML export formatting helpers."""

import csv
from io import StringIO
from xml.sax.saxutils import escape

from property_hunter.domain.models import AnalyzedProperty


def properties_to_csv(properties: list[AnalyzedProperty]) -> str:
    """Format analyzed properties as CSV.

    Parameters
    ----------
    properties:
        Stored analyzed property records.

    Returns
    -------
    str
        CSV document with one property per row.
    """
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "title",
            "url",
            "price",
            "price_per_sqm",
            "area_sqm",
            "parcel_id",
            "city",
            "street",
            "latitude",
            "longitude",
            "sync_status",
        ],
    )
    writer.writeheader()
    for item in properties:
        latitude = longitude = None
        if item.geometry is not None:
            latitude, longitude = item.geometry.centroid_wgs84
        writer.writerow(
            {
                "id": item.id,
                "title": item.listing.title,
                "url": str(item.listing.url),
                "price": item.extracted.price,
                "price_per_sqm": item.extracted.price_per_sqm,
                "area_sqm": item.extracted.area_sqm,
                "parcel_id": item.extracted.parcel_id,
                "city": item.extracted.city,
                "street": item.extracted.street,
                "latitude": latitude,
                "longitude": longitude,
                "sync_status": item.sync_status.value,
            }
        )
    return output.getvalue()


def properties_to_kml(properties: list[AnalyzedProperty]) -> str:
    """Format analyzed properties with coordinates as KML placemarks.

    Parameters
    ----------
    properties:
        Stored analyzed property records.

    Returns
    -------
    str
        KML document containing placemarks for properties with geometry.
    """
    placemarks = []
    for item in properties:
        if item.geometry is None:
            continue
        latitude, longitude = item.geometry.centroid_wgs84
        description = escape(str(item.listing.url))
        name = escape(item.listing.title)
        placemarks.append(
            "<Placemark>"
            f"<name>{name}</name>"
            f"<description>{description}</description>"
            "<Point>"
            f"<coordinates>{longitude:.7f},{latitude:.7f},0</coordinates>"
            "</Point>"
            "</Placemark>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2">'
        "<Document>"
        f"{''.join(placemarks)}"
        "</Document>"
        "</kml>"
    )
