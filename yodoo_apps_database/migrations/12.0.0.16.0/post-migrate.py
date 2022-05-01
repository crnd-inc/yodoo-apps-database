from odoo import api, SUPERUSER_ID


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for odoo_serie in ['14.0']:
        env['yodoo.serie'].get_or_create(odoo_serie)
