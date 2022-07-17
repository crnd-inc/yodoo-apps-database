from odoo.addons.yodoo_apps_database.tools.migration_utils import (
    sync_module_info_data,
    create_or_update_serie,
)
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.38.0')
def migrate(cr, installed_version):
    create_or_update_serie(cr, 15, 0)
    sync_module_info_data(cr)
