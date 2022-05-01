import csv

from odoo.tools.misc import file_open


def sync_module_info_data(cr):
    """ Generate missing external identifiers (xmlids)
        for modules and module series that statisfies following conditions:
            - present in database
            - does not have XMLID
            - present in csv file
    """
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
                  AND NOT EXISTS (
                         SELECT 1 FROM ir_model_data
                         WHERE module = 'yodoo_apps_database'
                           AND name = %(id)s
                           AND model = 'yodoo.module')
            """, row)

    with file_open('yodoo_apps_database/data/yodoo.module.serie.csv') as f:
        actual_xmlids = []
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
                  AND NOT EXISTS (
                         SELECT 1 FROM ir_model_data
                         WHERE module = 'yodoo_apps_database'
                           AND name = %(id)s
                           AND model = 'yodoo.module.serie')

            """, row)
            actual_xmlids += [row['id']]

        # make removed modules 'noupdate' to avoid errors during upgrade
        # process
        cr.execute("""
            UPDATE ir_model_data
            SET noupdate=True
            WHERE module = 'yodoo_apps_database'
              AND model = 'yodoo.module.serie'
              AND name ILIKE 'odoo_community_module__%%__yodoo_serie__%%'
              AND name NOT IN %(actual_names)s;
        """, {
            'actual_names': tuple(actual_xmlids),
        })


def create_or_update_serie(cr, serie_major, serie_minor):
    serie = "%s.%s" % (serie_major, serie_minor)
    xmlid = "yodoo_serie__%s_%s" % (serie_major, serie_minor)
    cr.execute("""
        INSERT INTO yodoo_serie
            (name, major, minor, active)
        VALUES (%(serie)s, %(major)s, %(minor)s, True)
        ON CONFLICT (name) DO NOTHING;

        INSERT INTO ir_model_data
            (module, name, model, res_id)
        SELECT 'yodoo_apps_database',
                %(xmlid)s,
                'yodoo.serie',
                ys.id
        FROM yodoo_serie AS ys
        WHERE ys.name = %(serie)s
            AND NOT EXISTS (
                    SELECT 1 FROM ir_model_data
                    WHERE module = 'yodoo_apps_database'
                    AND name = %(xmlid)s
                    AND model = 'yodoo.serie')
    """, {
        'serie': serie,
        'major': serie_major,
        'minor': serie_minor,
        'xmlid': xmlid,
    })
