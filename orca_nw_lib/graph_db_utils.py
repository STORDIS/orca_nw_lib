from orca_nw_lib.utils import get_orca_config
from orca_nw_lib.constants import neo4j_url, neo4j_password, neo4j_user, protocol

from neomodel import config, db, clear_neo4j_database


def init_db_connection():
    config.DATABASE_URL = f"{get_orca_config().get(protocol)}://{get_orca_config().get(neo4j_user)}:{get_orca_config().get(neo4j_password)}@{get_orca_config().get(neo4j_url)}"


def clean_db():
    clear_neo4j_database(db)
