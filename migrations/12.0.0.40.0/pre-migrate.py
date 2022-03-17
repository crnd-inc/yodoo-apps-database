from odoo.addons.yodoo_apps_database.tools.migration_utils import (
    sync_module_info_data,
)


def migrate(cr, installed_version):
    sync_module_info_data(cr)
