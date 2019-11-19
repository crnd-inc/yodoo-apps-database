from odoo import models, fields


class YodooModuleSerie(models.Model):
    _inherit = 'yodoo.module.serie'

    product_variant_id = fields.Many2one(
        'product.product', 'Product Variant', readonly=True)
