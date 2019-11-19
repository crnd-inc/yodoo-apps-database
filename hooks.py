from odoo import api, SUPERUSER_ID


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Serie = env['yodoo.serie']
    for serie in Serie.with_context(active_test=False).search([]):
        serie.product_attribute_value_id = Serie._generate_product_attribute(
            serie.name)
