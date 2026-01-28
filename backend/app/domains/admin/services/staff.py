from advanced_alchemy.extensions.litestar import repository, service
from app.db import models as m


class StaffService(service.SQLAlchemyAsyncRepositoryService[m.SessionStaff]):
    """Location service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.SessionStaff]):
        """Location repository."""

        model_type = m.SessionStaff

    repository_type = Repo
