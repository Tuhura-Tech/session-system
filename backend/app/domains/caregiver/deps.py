from __future__ import annotations

from sqlalchemy.orm import joinedload, load_only, selectinload

from app.db import models as m

from app.domains.caregiver.services.caregiver import CaregiverService
from app.lib.deps import create_service_provider

provide_caregiver_service = create_service_provider(
    CaregiverService,
    error_messages={
        "duplicate_key": "User with this email already exists.",
        "integrity": "User operation failed.",
    },
)
