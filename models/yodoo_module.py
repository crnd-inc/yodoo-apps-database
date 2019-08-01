import logging
from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)


class OdooModule(models.Model):
    _name = 'yodoo.module'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'generic.tag.mixin',
        'generic.resource.mixin',
    ]
    _description = "Odoo Module"
    _order = 'name, system_name'

    system_name = fields.Char(required=True, readonly=True, index=True)
    module_serie_ids = fields.One2many(
        'yodoo.module.serie', 'module_id', readonly=True)
    version_ids = fields.One2many(
        'yodoo.module.version', 'module_id', readonly=True)
    version_count = fields.Integer(
        compute='_compute_last_version',
        store=True, readonly=True)
    last_version_id = fields.Many2one(
        'yodoo.module.version', readonly=True, store=True,
        compute='_compute_last_version')
    serie_ids = fields.Many2many(
        string="Series",
        comodel_name='yodoo.serie',
        relation="yodoo_module_serie_rel",
        column1="module_id", column2='serie_id',
        readonly=True, store=True,
        compute='_compute_serie_ids', compute_sudo=True)
    serie_count = fields.Integer(
        compute='_compute_serie_ids', store=True,
        readonly=True, compute_sudo=True)

    license_id = fields.Many2one(
        'yodoo.module.license', index=True,
        related='last_version_id.license_id', store=True, readonly=True)
    category_id = fields.Many2one(
        'yodoo.module.category', index=True,
        related='last_version_id.category_id', store=True, readonly=True)
    author_ids = fields.Many2manyView(
        comodel_name='yodoo.module.author',
        relation='yodoo_module_author_rel_view',
        column1='module_id', column2='author_id',
        readonly=True)
    dependency_ids = fields.Many2manyView(
        comodel_name='yodoo.module',
        relation='yodoo_module_dependency_rel_view',
        column1='module_id', column2='dependency_id',
        readonly=True)
    dependency_all_ids = fields.Many2manyView(
        comodel_name='yodoo.module',
        relation='yodoo_module_dependency_all_rel_view',
        column1='module_id',
        column2='dependency_id',
        readonly=True)

    name = fields.Char(
        related='last_version_id.name', store=True,
        readonly=True, index=True)
    version = fields.Char(
        related='last_version_id.version', store=True,
        readonly=True)
    summary = fields.Char(
        related='last_version_id.summary', store=True,
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
    # icon = fields.Char(readonly=True)
    website = fields.Char(
        related='last_version_id.website', store=True,
        readonly=True)
    price = fields.Monetary(
        related='last_version_id.price', store=True,
        readonly=True)
    total_price = fields.Monetary(
        compute='_compute_total_price', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', related='last_version_id.currency_id', store=True,
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

    @api.depends('module_serie_ids')
    def _compute_serie_ids(self):
        for record in self:
            record.serie_ids = record.module_serie_ids.mapped('serie_id')
            record.serie_count = len(record.serie_ids)

    @api.depends('dependency_ids', 'dependency_all_ids.price',
                 'dependency_all_ids.currency_id',
                 'dependency_all_ids.last_version_id.dependency_ids',
                 'last_version_id.dependency_ids')
    def _compute_total_price(self):
        Version = self.env['yodoo.module.version']
        default_currency = Version.get_default_currency()
        date = self._context.get('date', fields.Date.today())
        company = self.env['res.company'].browse(
            self._context.get(
                'company_id', self.env.user.company_id.id))
        for record in self:
            price = record.price
            currency = record.currency_id or default_currency
            for dep in record.dependency_all_ids:
                if not dep.price:
                    continue
                dep_currency = dep.currency_id or default_currency
                price += dep_currency._convert(
                    dep.price, currency, company, date)
            record.total_price = price

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res += [(
                record.id,
                "%s" % (record.name or record.system_name),
            )]
        return res

    @api.model
    @tools.ormcache('system_name')
    def _get_module_id(self, system_name):
        module = self.with_context(active_test=False).search(
            [('system_name', '=', system_name)], limit=1)
        if module:
            return module.id
        return False

    @api.model
    def get_or_create_module(self, system_name):
        module_id = self._get_module_id(system_name)
        if module_id:
            return self.browse(module_id)
        module = self.with_context(
            mail_create_nosubscribe=True,
            mail_create_nolog=True,
            mail_notrack=True,
        ).create({
            'system_name': system_name,
        })
        self._get_module_id.clear_cache(self)
        return module

    @api.model
    @api.returns('yodoo.module.version')
    def create_or_update_module(self, system_name, data, no_update=False):
        """ Create or update module and return created/updated version
        """
        module = self.get_or_create_module(system_name)
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

    @api.multi
    def action_show_module_series(self):
        self.ensure_one()
        action = self.env.ref(
            'yodoo_apps_database.action_yodoo_module_serie_view').read()[0]
        action.update({
            'domain': [('module_id', '=', self.id)],
        })
        return action
