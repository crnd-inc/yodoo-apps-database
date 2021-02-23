import logging
from odoo.osv import expression
from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)

# List of fields to sync from last version
VERSION_TO_MODULE_SYNC_FIELDS = [
    'license_id',
    'category_id',
    'name',
    'version',
    'summary',
    'application',
    'installable',
    'auto_install',
    # 'icon',
    'website',
    'price',
    'currency_id',
]

# Check module_version for list of fields to be synced from module version
# model


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
    _log_access = False

    system_name = fields.Char(required=True, readonly=True, index=True)
    module_serie_ids = fields.One2many(
        'yodoo.module.serie', 'module_id', readonly=False)
    version_ids = fields.One2many(
        'yodoo.module.version', 'module_id', readonly=True)
    version_count = fields.Integer(
        store=True, readonly=True)
    last_version_id = fields.Many2one(
        'yodoo.module.version', readonly=True, store=True)
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
        'yodoo.module.license', index=True, store=True, readonly=True)
    category_id = fields.Many2one(
        'yodoo.module.category', index=True, store=True, readonly=True)
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
    dependency_of_ids = fields.Many2manyView(
        comodel_name='yodoo.module',
        relation='yodoo_module_dependency_all_rel_view',
        column1='dependency_id',
        column2='module_id',
        readonly=True)

    # This fields will be computed automatically on version update
    name = fields.Char(
        store=True, readonly=True, index=True)
    version = fields.Char(
        store=True, readonly=True)
    summary = fields.Char(
        store=True, readonly=True)
    application = fields.Boolean(
        store=True, readonly=True)
    installable = fields.Boolean(
        store=True, readonly=True)
    auto_install = fields.Boolean(
        store=True, readonly=True)
    # icon = fields.Char(readonly=True)
    website = fields.Char(
        store=True, readonly=True)
    price = fields.Monetary(
        store=True, readonly=True)
    total_price = fields.Monetary(
        compute='_compute_total_price', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', store=True, readonly=True)

    odoo_apps_link = fields.Char(
        compute='_compute_odoo_apps_link', store=True, readonly=True)

    is_odoo_community_addon = fields.Boolean(
        store=True, readonly=True,
        compute='_compute_is_odoo_community_addon',
        help='If set, then this module is part of Odoo Community')

    _sql_constraints = [
        ('system_name_uniq',
         'unique(system_name)',
         'Module system name must be uniqe!')
    ]

    @api.depends('module_serie_ids', 'module_serie_ids.odoo_apps_link')
    def _compute_odoo_apps_link(self):
        for record in self:
            odoo_apps_link = False
            for serie in record.module_serie_ids.sorted():
                if serie.odoo_apps_link:
                    odoo_apps_link = serie.odoo_apps_link
                    break
            record.odoo_apps_link = odoo_apps_link

    @api.depends('module_serie_ids')
    def _compute_serie_ids(self):
        for record in self:
            record.serie_ids = record.module_serie_ids.mapped('serie_id')
            record.serie_count = len(record.serie_ids)

    @api.depends('module_serie_ids.is_odoo_community_addon')
    def _compute_is_odoo_community_addon(self):
        for record in self:
            module_series = record.with_context(
                active_test=False
            ).module_serie_ids
            if not module_series:
                record.is_odoo_community_addon = False
            else:
                record.is_odoo_community_addon = (
                    module_series.sorted()[0].is_odoo_community_addon)

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []

        args = expression.AND([
            args,
            expression.OR([
                [('name', operator, name)],
                [('system_name', operator, name)],
            ]),
        ])
        return self.search(args, limit=limit).sudo().name_get()

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
            'active': True,
        })
        self._get_module_id.clear_cache(self)
        return module

    def get_module_serie(self, serie):
        """ Get 'yodoo.module.serie' for specified serie

            :param serie: could be ID, name, or record for corresponding
                          yodoo.serie model
            :return: instance of yodoo.module.serie. Could be empty recordset
                     if such module serie was not found
        """
        self.ensure_one()
        if isinstance(serie, int):
            serie_obj = self.env['yodoo.serie'].browse(serie)
        elif isinstance(serie, str):
            serie_obj = self.env['yodoo.serie'].get_serie(serie)
        elif isinstance(serie, models.Model) and serie._name == 'yodoo.serie':
            serie_obj = serie

        return self.env['yodoo.module.serie'].get_module_serie(
            self.id, serie_obj.id)

    @api.model
    @api.returns('yodoo.module.version')
    def create_or_update_module(self, system_name, data, no_update=False):
        """ Create or update module and return created/updated version
        """
        module = self.get_or_create_module(system_name)
        version = self.env['yodoo.module.version'].create_or_update_version(
            module, data, no_update=no_update)
        return version

    def check_odoo_apps_published_state(self):
        self.mapped('module_serie_ids').check_odoo_apps_published_state()

    @api.model
    def resolve_module_deps_for_serie(self, modules, serie,
                                      known_modules=None):
        """ Resolve module dependencies for specified serie

            :param RecordSet('yodoo.module') modules: List of modules
                to resolve dependencies for
            :param RecordSet('yodoo.serie') serie: Serie to resolve deps for
            :param RecordSet('yodoo.module') known_modules: List of knonw
                modules that assumed already available, and do not need
                to be mentioned in result
            :return typle: tuple (modules, module_series) that containse all
                resolved modules and module_series, except odoo's standard
                modules
        """
        if not known_modules:
            known_modules = self.env['yodoo.module'].browse()

        module_series = modules.mapped('module_serie_ids').filtered(
            lambda r: r.serie_id == serie)
        all_module_series = module_series + module_series.mapped(
            'dependency_all_ids')

        res_modules = self.env['yodoo.module'].browse()
        res_module_series = self.env['yodoo.module.serie'].browse()
        for module_serie in all_module_series:
            if module_serie.is_odoo_community_addon:
                # Skip community modules
                continue
            if module_serie.module_id in known_modules:
                # Skip known modules
                continue
            if module_serie.module_id not in res_modules:
                res_modules += module_serie.module_id
                res_module_series += module_serie

        return res_modules, res_module_series

    def action_show_versions(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_version_view',
            domain=[('module_id', '=', self.id)])

    def action_show_module_series(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_serie_view',
            domain=[('module_id', '=', self.id)])
