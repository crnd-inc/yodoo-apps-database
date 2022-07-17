from odoo import api, SUPERUSER_ID
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.5.0')
def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for odoo_serie in ['8.0', '9.0', '10.0', '11.0', '12.0', '13.0', '14.0']:
        env['yodoo.serie'].get_or_create(odoo_serie)
