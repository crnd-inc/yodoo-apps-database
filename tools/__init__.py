from psycopg2 import sql
from odoo import tools


def create_sql_view(cr, name, definition):
    # pylint: disable=sql-injection
    tools.drop_view_if_exists(cr, name)
    cr.execute(sql.SQL("""
        CREATE or REPLACE VIEW {name} AS ({definition});
    """).format(name=sql.Identifier(name), definition=sql.SQL(definition)))
