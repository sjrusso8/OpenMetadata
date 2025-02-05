#  Copyright 2021 Collate
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Source connection handler
"""
import sys
from urllib.parse import quote_plus

import oracledb
from pydantic import SecretStr
from sqlalchemy.engine import Engine

from metadata.generated.schema.entity.services.connections.database.oracleConnection import (
    OracleConnection,
    OracleDatabaseSchema,
    OracleServiceName,
)
from metadata.ingestion.connections.builders import (
    create_generic_db_connection,
    get_connection_args_common,
)
from metadata.ingestion.connections.test_connections import test_connection_db_common

CX_ORACLE_LIB_VERSION = "8.3.0"


def get_connection_url(connection: OracleConnection) -> str:
    """
    Build the URL and handle driver version at system level
    """

    oracledb.version = CX_ORACLE_LIB_VERSION
    sys.modules["cx_Oracle"] = oracledb

    url = f"{connection.scheme.value}://"
    if connection.username:
        url += f"{quote_plus(connection.username)}"
        if not connection.password:
            connection.password = SecretStr("")
        url += f":{quote_plus(connection.password.get_secret_value())}"
        url += "@"

    url += connection.hostPort

    if isinstance(connection.oracleConnectionType, OracleDatabaseSchema):
        url += (
            f"/{connection.oracleConnectionType.databaseSchema}"
            if connection.oracleConnectionType.databaseSchema
            else ""
        )

    elif isinstance(connection.oracleConnectionType, OracleServiceName):
        url = f"{url}/?service_name={connection.oracleConnectionType.oracleServiceName}"

    options = (
        connection.connectionOptions.dict()
        if connection.connectionOptions
        else connection.connectionOptions
    )
    if options:
        params = "&".join(
            f"{key}={quote_plus(value)}" for (key, value) in options.items() if value
        )
        if isinstance(connection.oracleConnectionType, OracleServiceName):
            url = f"{url}&{params}"
        else:
            url = f"{url}?{params}"

    return url


def get_connection(connection: OracleConnection) -> Engine:
    """
    Create connection
    """
    return create_generic_db_connection(
        connection=connection,
        get_connection_url_fn=get_connection_url,
        get_connection_args_fn=get_connection_args_common,
    )


def test_connection(engine: Engine) -> None:
    """
    Test connection
    """
    test_connection_db_common(engine)
