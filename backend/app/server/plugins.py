from functools import cache

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from app.lib.settings import saq_settings, sqlalchemy_settings

# from app import config
# from app.utils.domain import DomainPlugin
from app.utils.oauth import OAuth2ProviderPlugin

alchemy = SQLAlchemyPlugin(config=sqlalchemy_settings)
granian = GranianPlugin()
oauth2_provider = OAuth2ProviderPlugin()
# domain = DomainPlugin()


@cache
def get_saq_plugin() -> SAQPlugin:
    """Get SAQ plugin lazily to avoid Redis connection during build."""
    # return SAQPlugin(config=config.get_saq_config())
    return SAQPlugin(config=saq_settings)
