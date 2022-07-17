from odoo import api, SUPERUSER_ID
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.16.0')
def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for odoo_serie in ['14.0']:
        env['yodoo.serie'].get_or_create(odoo_serie)
