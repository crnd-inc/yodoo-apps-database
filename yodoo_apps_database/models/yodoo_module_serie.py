import logging
from pkg_resources import parse_version as V

from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)


class OdooModuleSerie(models.Model):
    _name = 'yodoo.module.serie'
    _description = "Odoo Module Serie"
    _order = "module_id, serie_major DESC, serie_minor DESC"
    _log_access = False

    module_id = fields.Many2one(
        'yodoo.module', required=True, readonly=True, index=True,
        ondelete='cascade')
    serie_id = fields.Many2one(
        'yodoo.serie', required=True, readonly=True, index=True,
        ondelete='cascade')
    serie_major = fields.Integer(
        related='serie_id.major', store=True, index=True, readonly=True)
    serie_minor = fields.Integer(
        related='serie_id.minor', store=True, index=True, readonly=True)

    # Version
    version_ids = fields.One2many(
        'yodoo.module.version', 'module_serie_id', readonly=True)
    version_count = fields.Integer(
        store=True, readonly=True)
    last_version_id = fields.Many2one(
        'yodoo.module.version', readonly=True, store=True, index=True)

    # Following fields are not stored for performance reasons
    license_id = fields.Many2one(
        'yodoo.module.license', index=False, store=False,
        related='last_version_id.license_id',
        readonly=True)
    category_id = fields.Many2one(
        'yodoo.module.category', index=False, store=False,
        related='last_version_id.category_id',
        readonly=True)
    installable = fields.Boolean(
        related='last_version_id.installable', readonly=True)

    odoo_apps_link = fields.Char(
        help="Link to addon's page on Odoo Apps",
        readonly=True)
    is_odoo_community_addon = fields.Boolean(
        default=False, readonly=True, index=True)

    dependency_ids = fields.Many2manyView(
        comodel_name='yodoo.module.serie',
        relation='yodoo_module_serie_dependency_rel_view',
        column1='module_serie_id',
        column2='dependency_module_serie_id',
        readonly=True)
    dependency_all_ids = fields.Many2manyView(
        comodel_name='yodoo.module.serie',
        relation='yodoo_module_serie_dependency_all_rel_view',
        column1='module_serie_id',
        column2='dependency_module_serie_id',
        readonly=True)
    dependency_of_ids = fields.Many2manyView(
        comodel_name='yodoo.module.serie',
        relation='yodoo_module_serie_dependency_rel_view',
        column1='dependency_module_serie_id',
        column2='module_serie_id',
        readonly=True)
    dependency_of_all_ids = fields.Many2manyView(
        comodel_name='yodoo.module.serie',
        relation='yodoo_module_serie_dependency_all_rel_view',
        column1='dependency_module_serie_id',
        column2='module_serie_id',
        readonly=True)

    # External dependencies
    dependency_python_ids = fields.Many2manyView(
        comodel_name='yodoo.module.dependency.python',
        relation='yodoo_module_serie_dependency_python_rel_view',
        column1='module_serie_id',
        column2='dependency_id',
        string="Python dependencies",
        readonly=True)
    dependency_bin_ids = fields.Many2manyView(
        comodel_name='yodoo.module.dependency.binary',
        relation='yodoo_module_serie_dependency_binary_rel_view',
        column1='module_serie_id',
        column2='dependency_id',
        string="Binary dependencies",
        readonly=True)

    _sql_constraints = [
        ('module_serie_uniq',
         'unique(module_id, serie_id)',
         'Module and serie must be unique!'),
    ]

    def _check_need_update_last_version(self, new_version):
        """ Determine if we need to update last version of this module serie
            or not.

            :param Record new_version: Record that represents new version
            :return bool: True if new version is good to update,
                 otherwise False
        """
        if not self.last_version_id:
            return True
        if V(self.last_version_id.version) < V(new_version.version):
            return True
        return False

    def name_get(self):
        res = []
        for record in self:
            res += [(
                record.id,
                "%s [%s]" % (record.module_id.system_name,
                             record.serie_id.display_name),
            )]
        return res

    @api.model
    def get_module_serie(self, module_id, serie_id):
        return self.with_context(active_test=False).search(
            [('module_id', '=', module_id),
             ('serie_id', '=', serie_id)],
            limit=1)

    @api.model
    def get_or_create(self, module_id, serie_id):
        module_serie = self.get_module_serie(module_id, serie_id)
        if not module_serie:
            module_serie = self.create({
                'module_id': module_id,
                'serie_id': serie_id,
            })
        return module_serie

    def check_odoo_apps_published_state(self):
        from requests_futures.sessions import FuturesSession

        session = FuturesSession()
        results = {}
        links = {}
        for record in self:
            link = "https://apps.odoo.com/apps/modules/%(serie)s/%(name)s/" % {
                'serie': record.serie_id.name,
                'name': record.module_id.system_name,
            }
            links[record] = link
            results[record] = session.head(link)

        for record, future in results.items():
            if future.result().status_code == 200:
                record.odoo_apps_link = links[record]
            else:
                record.odoo_apps_link = False

    @api.model
    def scheduler_test_odoo_apps_link(self):
        records = self.search(
            [('odoo_apps_link', '=', False)]
        )

        for record_ids in tools.split_every(1000, records.ids):
            with api.Environment.manage():
                with self.env.registry.cursor() as new_cr:
                    new_env = api.Environment(new_cr, self.env.uid,
                                              self.env.context.copy())
                    try:
                        new_env[self._name].browse(
                            record_ids).check_odoo_apps_published_state()
                    except Exception:
                        _logger.error(
                            "Error caught when trying to check publishing "
                            "state of module series %s",
                            record_ids, exc_info=True)
                        new_cr.rollback()
                    else:
                        new_cr.commit()

    def action_show_versions(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_version_view',
            domain=[('module_serie_id', '=', self.id)])
