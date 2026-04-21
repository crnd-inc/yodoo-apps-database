from odoo import models, fields


class YodooModuleCategory(models.Model):
    _inherit = 'yodoo.module.category'

    is_published = fields.Boolean(
        string='Published',
        default=True,
        help='If unchecked, every module in this category is hidden from '
             'the website (404 even on direct URL).',
    )
    is_listed_on_website = fields.Boolean(
        string='Listed on Website',
        default=True,
        help='If unchecked, modules of this category are excluded from '
             '/modules listing and search, but still accessible by '
             'direct URL.',
    )
