from odoo import models, fields, api, tools
from ..tools import create_sql_view


class YodooModuleAuthor(models.Model):
    _name = 'yodoo.module.author'
    _description = "Yodoo Module Author"
    _order = 'name'
    _log_access = False

    name = fields.Char(required=True, index=True)
    color = fields.Selection([
        (1, "Red"),
        (2, "Orange"),
        (3, "Yellow"),
        (4, "Light blue"),
        (5, "Dark purple"),
        (6, "Salmon pink"),
        (7, "Medium blue"),
        (8, "Dark blue"),
        (9, "Fushia"),
        (10, "Green"),
        (11, "Purple")])
    partner_id = fields.Many2one(
        'res.partner', 'Associated Partner')

    version_ids = fields.Many2many(
        comodel_name='yodoo.module.version',
        relation='yodoo_module_version_author_rel',
        column1='author_id', column2='version_id',
        readonly=True)
    module_ids = fields.Many2manyView(
        comodel_name='yodoo.module',
        relation='yodoo_module_author_rel_view',
        column1='author_id', column2='module_id',
        readonly=True)
    module_count = fields.Integer(
        compute='_compute_module_count', readonly=True)

    _sql_constraints = [
        ('module_name_uniq',
         'unique(name)',
         'Author name must be unique!'),
    ]

    @api.depends('module_ids')
    def _compute_module_count(self):
        for record in self:
            record.module_count = len(record.module_ids)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'yodoo_module_author_rel_view')
        create_sql_view(
            self.env.cr, 'yodoo_module_author_rel_view',
            """
                SELECT DISTINCT
                    mv.module_id,
                    va_rel.author_id
                FROM yodoo_module_version_author_rel AS va_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = va_rel.version_id
                LEFT JOIN yodoo_module AS mod
                    ON mv.module_id = mod.id
                WHERE mv.id = mod.last_version_id
        """)
        return super(YodooModuleAuthor, self).init()

    @api.model
    @tools.ormcache('name')
    def _get_author(self, name):
        author = self.with_context(active_test=False).search(
            [('name', '=', name)], limit=1)
        if author:
            return author.id
        return False

    @api.model
    def get_or_create(self, name):
        author_id = self._get_author(name)
        if not author_id:
            author_id = self.create({
                'name': name,
            }).id
            self._get_author.clear_cache(self)
        return author_id

    def action_show_modules(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_view',
            domain=[('author_ids.id', '=', self.id)])
