from advanced_alchemy.extensions.litestar import repository, service
from app.db import models as m


class StudentService(service.SQLAlchemyAsyncRepositoryService[m.Child]):
    """Location service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.Child]):
        """Location repository."""

        model_type = m.Child

    repository_type = Repo
