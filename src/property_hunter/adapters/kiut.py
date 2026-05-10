"""KIUT/GESUT utility assessment adapter."""

from property_hunter.domain.geo import classify_utility_distance
from property_hunter.domain.models import ParcelGeometry, UtilityAssessment


class KIUTUtilitySource:
    """Conservative KIUT placeholder until exact public WFS layers are verified."""

    def assess(self, geometry: ParcelGeometry) -> list[UtilityAssessment]:
        """Return unknown statuses for expected utility networks.

        KIUT public documentation emphasizes WMS access. This adapter keeps the
        orchestration contract live while avoiding false precision until usable
        feature access is configured.
        """
        _ = geometry
        return [
            UtilityAssessment(
                network_type=network_type,
                status=classify_utility_distance(None),
                source_layer="KIUT/GESUT",
            )
            for network_type in ("water", "sewage", "electricity", "gas")
        ]
