from advanced_alchemy.extensions.litestar import repository, service
from app.db import models as m


class OccurrenceService(service.SQLAlchemyAsyncRepositoryService[m.SessionOccurrence]):
    """Location service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.SessionOccurrence]):
        """Location repository."""

        model_type = m.SessionOccurrence

    repository_type = Repo
