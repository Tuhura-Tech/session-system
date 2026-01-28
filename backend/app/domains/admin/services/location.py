from advanced_alchemy.extensions.litestar import repository, service
from app.db import models as m


class LocationService(service.SQLAlchemyAsyncRepositoryService[m.SessionLocation]):
    """Location service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.SessionLocation]):
        """Location repository."""

        model_type = m.SessionLocation

    repository_type = Repo
