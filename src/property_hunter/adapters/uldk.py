"""GUGiK ULDK parcel lookup adapter."""

import httpx
from pyproj import Transformer
from shapely import wkt
from tenacity import retry, stop_after_attempt, wait_exponential

from property_hunter.domain.models import ParcelGeometry


class ULDKParcelLocator:
    """Resolve cadastral parcel geometry through GUGiK ULDK."""

    def __init__(
        self,
        base_url: str = "https://uldk.gugik.gov.pl/",
        timeout_seconds: float = 15.0,
    ) -> None:
        """Create a ULDK client."""
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self._transformer = Transformer.from_crs(
            "EPSG:2180",
            "EPSG:4326",
            always_xy=True,
        )

    @retry(wait=wait_exponential(multiplier=0.5, max=4), stop=stop_after_attempt(3))
    def locate(self, parcel_id: str) -> ParcelGeometry | None:
        """Resolve a parcel id to geometry."""
        response = httpx.get(
            self.base_url,
            params={
                "request": "GetParcelById",
                "id": parcel_id,
                "result": "geom_wkt",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        geometry_wkt = _extract_wkt(response.text)
        if geometry_wkt is None:
            return None
        geometry = wkt.loads(geometry_wkt)
        centroid = geometry.centroid
        longitude, latitude = self._transformer.transform(centroid.x, centroid.y)
        return ParcelGeometry(
            parcel_id=parcel_id,
            centroid_2180=(centroid.x, centroid.y),
            centroid_wgs84=(latitude, longitude),
            wkt=geometry_wkt,
        )


def _extract_wkt(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith(("POLYGON", "MULTIPOLYGON")):
            return stripped
        if "|" in stripped:
            candidate = stripped.rsplit("|", maxsplit=1)[-1].strip()
            if candidate.upper().startswith(("POLYGON", "MULTIPOLYGON")):
                return candidate
    return None
