import ast

from lxml import etree

from odoo.tests.common import TransactionCase


class TestGitSourceTaskWidgetFields(TransactionCase):
    """ generic_task_queue's gtq_task_auto_refresh widget reads its
        state_field / progress_field options as plain keys of
        record.data (task_auto_refresh_field.js: setup(), extractProps())
        — it does not resolve dotted paths such as
        'last_sync_task_id.state'. yodoo.git.source must expose plain
        related fields for the widget to read, and the view must
        reference those field names (and declare them so they end up
        in record.data).
    """

    def setUp(self):
        super().setUp()
        self.source = self.env['yodoo.git.source'].create({
            'name': 'Test Source Widget Fields',
        })
        self.task = self.env['generic.task.queue.task'].sudo().create_task(
            'yodoo_apps_website.source_sync',
            name='Sync Test Source Widget Fields',
            params={'source_id': self.source.id},
        )
        self.source.sudo().last_sync_task_id = self.task

    def test_related_fields_mirror_task_state_and_progress(self):
        self.task.sudo().write({'state': 'running', 'progress': 42})
        self.source.invalidate_recordset()
        self.assertEqual(self.source.last_sync_task_state, 'running')
        self.assertEqual(self.source.last_sync_task_progress, 42)

    def test_related_fields_follow_task_reassignment(self):
        """ Negative control: after the task changes, the related fields
            reflect the NEW task's values, not stale ones left over from
            the previous task. """
        self.task.sudo().write({'state': 'done', 'progress': 100})

        other_task = self.env['generic.task.queue.task'].sudo().create_task(
            'yodoo_apps_website.source_sync',
            name='Second Sync Test Source Widget Fields',
            params={'source_id': self.source.id},
        )
        other_task.sudo().write({'state': 'pending', 'progress': 7})
        self.source.sudo().last_sync_task_id = other_task
        self.source.invalidate_recordset()

        self.assertEqual(self.source.last_sync_task_state, 'pending')
        self.assertEqual(self.source.last_sync_task_progress, 7)

    def test_view_widget_options_reference_plain_field_names(self):
        """ Arch test: the gtq_task_auto_refresh options must point at
            plain field names that are both declared on the model and
            present in the combined view's field list — not a dotted
            path through the last_sync_task_id relation. """
        view = self.env['yodoo.git.source'].get_view(view_type='form')
        arch = etree.fromstring(view['arch'])
        widget_fields = arch.xpath(
            "//field[@widget='gtq_task_auto_refresh']")
        self.assertEqual(len(widget_fields), 1)

        options = ast.literal_eval(widget_fields[0].get('options'))
        state_field = options['state_field']
        progress_field = options['progress_field']
        view_fields = view['models'][self.source._name]

        self.assertNotIn('.', state_field)
        self.assertNotIn('.', progress_field)
        self.assertIn(state_field, view_fields)
        self.assertIn(progress_field, view_fields)
