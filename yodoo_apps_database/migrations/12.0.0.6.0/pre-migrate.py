import csv
from odoo.tools.misc import file_open
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.6.0')
def migrate(cr, installed_version):
    with file_open('yodoo_apps_database/data/yodoo.module.csv') as f:
        for row in csv.DictReader(f):
            cr.execute("""
                INSERT INTO ir_model_data
                    (module, name, model, res_id)
                SELECT 'yodoo_apps_database',
                       %(id)s,
                       'yodoo.module',
                        ym.id
                FROM yodoo_module AS ym
                WHERE ym.system_name = %(system_name)s
            """, row)

    with file_open('yodoo_apps_database/data/yodoo.module.serie.csv') as f:
        for row in csv.DictReader(f):
            cr.execute("""
                INSERT INTO ir_model_data
                    (module, name, model, res_id)
                SELECT 'yodoo_apps_database',
                       %(id)s,
                       'yodoo.module.serie',
                        yms.id
                FROM yodoo_module_serie AS yms
                LEFT JOIN ir_model_data AS ym_data ON (
                       ym_data.res_id = yms.module_id AND
                       ym_data.module = 'yodoo_apps_database' AND
                       ym_data.model = 'yodoo.module')
                LEFT JOIN ir_model_data AS ys_data ON (
                       ys_data.res_id = yms.serie_id AND
                       ys_data.module = 'yodoo_apps_database' AND
                       ys_data.model = 'yodoo.serie')
                WHERE ym_data.name = %(module_id:id)s
                  AND ys_data.name = %(serie_id:id)s
            """, row)
