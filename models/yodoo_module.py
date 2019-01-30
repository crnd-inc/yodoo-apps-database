from odoo import models, fields, api


class OdooModule(models.Model):
    _name = 'yodoo.module'
    _inherit = [
        'mail.thread',
    ]
    _description = "Odoo Module"
    _order = 'name, system_name'

    system_name = fields.Char(required=True, readonly=True, index=True)
    version_ids = fields.One2many(
        'yodoo.module.version', 'module_id', readonly=True)
    version_count = fields.Integer(
        compute='_compute_last_version',
        store=True, readonly=True)
    last_version_id = fields.Many2one(
        'yodoo.module.version', readonly=True, store=True,
        compute='_compute_last_version')
    serie_ids = fields.Many2many(
        'yodoo.serie', readonly=True, store=True,
        compute='_compute_serie_ids')

    name = fields.Char(
        related='last_version_id.name', store=True,
        readonly=True, index=True)
    version = fields.Char(
        related='last_version_id.version', store=True,
        readonly=True)
    author = fields.Char(
        related='last_version_id.author', store=True,
        readonly=True, index=True)
    summary = fields.Char(
        related='last_version_id.summary', store=True,
        readonly=True)
    license = fields.Char(
        related='last_version_id.license', store=True,
        readonly=True)
    application = fields.Boolean(
        related='last_version_id.application', store=True,
        readonly=True)
    installable = fields.Boolean(
        related='last_version_id.installable', store=True,
        readonly=True)
    auto_install = fields.Boolean(
        related='last_version_id.auto_install', store=True,
        readonly=True)
    category = fields.Char(
        related='last_version_id.category', store=True,
        readonly=True)
    # icon = fields.Char(readonly=True)
    website = fields.Char(
        related='last_version_id.website', store=True,
        readonly=True)

    _sql_constraints = [
        ('system_name_uniq',
         'unique(system_name)',
         'Module system name must be uniqe!')
    ]

    @api.depends('version_ids')
    def _compute_last_version(self):
        for record in self:
            last_version = self.env['yodoo.module.version'].search(
                [('module_id', '=', record.id)], limit=1)
            if last_version:
                record.last_version_id = last_version
            else:
                record.last_version_id = False
            record.version_count = len(record.version_ids)

    @api.depends('version_ids.serie_id')
    def _compute_serie_ids(self):
        for record in self:
            record.serie_ids = record.version_ids.mapped('serie_id')

    @api.model
    @api.returns('yodoo.module.version')
    def create_or_update_module(self, system_name, data, no_update=False):
        """ Create or update module and return created/updated version
        """
        module = self.with_context(active_test=False).search(
            [('system_name', '=', system_name)], limit=1)
        if not module:
            module = self.create({
                'system_name': system_name,
            })
        version = self.env['yodoo.module.version'].create_or_update_version(
            module, data, no_update=no_update)
        return version

    @api.multi
    def action_show_versions(self):
        self.ensure_one()
        action = self.env.ref(
            'yodoo_apps_database.action_yodoo_module_version_view').read()[0]
        action.update({
            'domain': [('module_id', '=', self.id)],
        })
        return action
