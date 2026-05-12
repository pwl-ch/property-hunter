"""KIUT/GESUT utility assessment adapter."""

import logging

from property_hunter.domain.geo import classify_utility_distance
from property_hunter.domain.models import ParcelGeometry, UtilityAssessment

logger = logging.getLogger(__name__)


class KIUTUtilitySource:
    """Conservative KIUT placeholder until exact public WFS layers are verified."""

    def assess(self, geometry: ParcelGeometry) -> list[UtilityAssessment]:
        """Return unknown statuses for expected utility networks.

        KIUT public documentation emphasizes WMS access. This adapter keeps the
        orchestration contract live while avoiding false precision until usable
        feature access is configured.
        """
        logger.info("Returning placeholder KIUT utility assessment")
        _ = geometry
        return [
            UtilityAssessment(
                network_type=network_type,
                status=classify_utility_distance(None),
                source_layer="KIUT/GESUT",
            )
            for network_type in ("water", "sewage", "electricity", "gas")
        ]
