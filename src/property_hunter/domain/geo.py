"""Pure geographic helpers for PropertyHunter."""

from urllib.parse import quote

from property_hunter.domain.models import ExternalLinks, ParcelGeometry, UtilityStatus


def classify_utility_distance(distance_meters: float | None) -> UtilityStatus:
    """Classify network distance into the project traffic-light scale.

    Parameters
    ----------
    distance_meters:
        Distance to the nearest utility geometry in meters, or ``None`` when
        the source is unavailable.

    Returns
    -------
    UtilityStatus
        ``green`` for 10 m or less, ``yellow`` for up to 100 m, ``red`` beyond
        100 m, and ``unknown`` when the distance is unavailable.
    """
    if distance_meters is None:
        return UtilityStatus.UNKNOWN
    if distance_meters <= 10:
        return UtilityStatus.GREEN
    if distance_meters <= 100:
        return UtilityStatus.YELLOW
    return UtilityStatus.RED


def build_external_links(
    parcel_id: str | None,
    geometry: ParcelGeometry | None,
) -> ExternalLinks:
    """Build map and cadastral links from known parcel data.

    Parameters
    ----------
    parcel_id:
        Polish cadastral parcel identifier.
    geometry:
        Resolved parcel geometry, if available.

    Returns
    -------
    ExternalLinks
        Links that can be displayed in the API or dashboard.
    """
    google_maps = None
    geoportal = None
    if geometry is not None:
        latitude, longitude = geometry.centroid_wgs84
        google_maps = f"https://www.google.com/maps?q={latitude:.7f},{longitude:.7f}"
        geoportal = (
            "https://mapy.geoportal.gov.pl/imap/Imgp_2.html"
            f"?identifyParcel={quote(geometry.parcel_id)}"
        )

    uldk = None
    if parcel_id:
        uldk = (
            "https://uldk.gugik.gov.pl/"
            f"?request=GetParcelById&id={quote(parcel_id)}&result=geom_wkt"
        )

    return ExternalLinks.model_validate(
        {"google_maps": google_maps, "geoportal": geoportal, "uldk": uldk}
    )
