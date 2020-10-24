import re
from odoo import models, fields, api, tools, exceptions, _

RE_SERIE = re.compile(r"^(?P<serie_major>\d+)\.(?P<serie_minor>\d+)$")


class YodooSerie(models.Model):
    _name = 'yodoo.serie'
    _description = "Odoo Serie"
    _order = "major DESC, minor DESC"
    _log_access = False

    name = fields.Char(
        compute='_compute_name',
        inverse='_inverse_name',
        readonly=True, store=True, index=True)
    major = fields.Integer(readonly=True)
    minor = fields.Integer(readonly=True)
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

    module_ids = fields.Many2many(
        comodel_name='yodoo.module',
        relation="yodoo_module_serie_rel",
        column1="serie_id", column2='module_id',
        readonly=True)
    module_count = fields.Integer(
        compute="_compute_module_count",
        readonly=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Serie name must be uniqe!')
    ]

    @api.model
    def _parse_serie_name(self, name):
        """ Parse serie by name and return dict with major and minor numbers
        """
        match = RE_SERIE.match(name)
        if match:
            res = match.groupdict()
            return {
                'major': res.get('serie_major', 0),
                'minor': res.get('serie_minor', 0),
            }
        else:
            return {
                'major': 0,
                'monor': 0,
            }

    @api.depends('major', 'minor')
    def _compute_name(self):
        for record in self:
            record.name = "%d.%d" % (record.major, record.minor)

    def _inverse_name(self):
        for record in self:
            record.update(self._parse_serie_name(self.name))

    @api.depends('module_ids')
    def _compute_module_count(self):
        for record in self:
            record.module_count = len(record.module_ids)

    @api.model
    @tools.ormcache('name')
    def _get_serie(self, name):
        serie = self.with_context(active_test=False).search(
            [('name', '=', name)], limit=1)
        if serie:
            return serie.id
        return False

    @api.model
    def get_serie(self, name):
        serie_id = self._get_serie(name)
        if serie_id:
            return self.browse(serie_id)
        return self.browse()

    def _create_serie(self, name):
        serie_data = {
            'name': name,
            'active': True,
        }
        serie_data.update(self._parse_serie_name(name))
        serie = self.create(serie_data)

        self.env['ir.model.data'].create({
            'module': 'yodoo_apps_database',
            'name': 'yodoo_serie__%s_%s' % (serie.major, serie.minor),
            'model': 'yodoo.serie',
            'res_id': serie.id,
            'noupdate': True,
        })
        return serie

    @api.model
    def get_or_create(self, name):
        if not RE_SERIE.match(name):
            raise exceptions.ValidationError(_(
                "Serie name ('%s') is not valid") % name)
        serie_id = self._get_serie(name)
        if not serie_id:
            serie_id = self._create_serie(name).id
            self._get_serie.clear_cache(self)
        return serie_id

    def action_show_modules(self):
        self.ensure_one()
        action = self.env.ref(
            'yodoo_apps_database.action_yodoo_module_view').read()[0]
        action.update({
            'domain': [('serie_ids.id', '=', self.id)],
        })
        return action
