from odoo.addons.yodoo_apps_database.tools.migration_utils import (
    sync_module_info_data,
    create_or_update_serie,
)


def migrate(cr, installed_version):
    create_or_update_serie(cr, 15, 0)
    sync_module_info_data(cr)
