from advanced_alchemy.extensions.litestar import repository, service
from app.db import models as m


class BlockService(service.SQLAlchemyAsyncRepositoryService[m.SessionBlock]):
    """Location service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.SessionBlock]):
        """Location repository."""

        model_type = m.SessionBlock

    repository_type = Repo
