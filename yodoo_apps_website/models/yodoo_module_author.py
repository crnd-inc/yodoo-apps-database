from odoo import models, fields


class YodooModuleAuthor(models.Model):
    _inherit = 'yodoo.module.author'

    # Restores BaseModel.CONCURRENCY_CHECK_FIELD removed in Odoo 18;
    # referenced by generic.mixin.refresh.view on every write.
    CONCURRENCY_CHECK_FIELD = '__last_update'

    is_published = fields.Boolean(
        string='Published',
        default=True,
        help='If unchecked, modules authored exclusively by this vendor are '
             'hidden from the website (404 even on direct URL). A module with '
             'multiple authors remains accessible if at least one author is '
             'published.',
    )
    is_listed_on_website = fields.Boolean(
        string='Listed on Website',
        default=False,
        help='If unchecked (default for authors), modules authored '
             'exclusively by this vendor are excluded from /modules '
             'listing and search, but still accessible by direct URL. '
             'A module with multiple authors remains listed as long '
             'as at least one of them has this flag enabled.',
    )
