import logging
from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)


class OdooModuleSerie(models.Model):
    _name = 'yodoo.module.serie'
    _description = "Odoo Module Serie"

    module_id = fields.Many2one(
        'yodoo.module', required=True, readonly=True, index=True,
        ondelete='cascade')
    serie_id = fields.Many2one(
        'yodoo.serie', required=True, readonly=True, index=True,
        ondelete='cascade')

    # Version
    version_ids = fields.One2many(
        'yodoo.module.version', 'module_serie_id', readonly=True)
    version_count = fields.Integer(
        store=True, readonly=True)
    last_version_id = fields.Many2one(
        'yodoo.module.version', readonly=True, store=True)

    # Following fields are not stored for performance reasons
    license_id = fields.Many2one(
        'yodoo.module.license', index=False, store=False,
        related='last_version_id.license_id',
        readonly=True)
    category_id = fields.Many2one(
        'yodoo.module.category', index=False, store=False,
        related='last_version_id.category_id',
        readonly=True)

    odoo_apps_link = fields.Char(
        help="Link to addon's page on Odoo Apps",
        readonly=True)

    _sql_constraints = [
        ('module_serie_uniq',
         'unique(module_id, serie_id)',
         'Module and serie must be unique!'),
    ]

    @api.multi
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
    def get_or_create(self, module_id, serie_id):
        module_serie = self.with_context(active_test=False).search(
            [('module_id', '=', module_id),
             ('serie_id', '=', serie_id)], limit=1)
        if not module_serie:
            module_serie = self.create({
                'module_id': module_id,
                'serie_id': serie_id,
            })
        return module_serie

    @api.multi
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
