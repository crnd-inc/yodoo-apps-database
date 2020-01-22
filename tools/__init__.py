from psycopg2 import sql
from odoo import tools


def create_sql_view(cr, name, definition):
    # pylint: disable=sql-injection
    tools.drop_view_if_exists(cr, name)
    query = sql.SQL("""
        CREATE or REPLACE VIEW {name} AS ({definition});
    """).format(name=sql.Identifier(name), definition=sql.SQL(definition))
    if getattr(cr, 'sql_log', None):
        query = query.as_string(cr._obj)
    cr.execute(query)
