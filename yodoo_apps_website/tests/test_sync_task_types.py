from unittest.mock import patch

from odoo.tests.common import TransactionCase

from ..services.sync_task_types import BRANCH_CHANNEL, YodooSourceSyncTaskType


class TestSourceSyncCreateChildren(TransactionCase):
    """ YodooSourceSyncTaskType.execute() must fan out exactly one
        branch_sync child per scannable branch, using create_children()'s
        homogeneous kwargs form (type_code / params_list / channel).
    """

    def setUp(self):
        super().setUp()
        self.Task = self.env['generic.task.queue.task']
        self.worker = self.env['generic.task.queue.worker'].create({
            'uuid': 'source-sync-test-worker',
            'service_name': 'test.service',
            'state': 'active',
        })
        self.source = self.env['yodoo.git.source'].create({
            'name': 'Test Source',
        })
        self.branches = self.env['yodoo.git.source.branch'].create([
            {
                'name': '18.0',
                'git_source_id': self.source.id,
                'yodoo_serie_id': self.env.ref(
                    'yodoo_apps_database.yodoo_serie__18_0').id,
                'scan': True,
            },
            {
                'name': '17.0',
                'git_source_id': self.source.id,
                'yodoo_serie_id': self.env.ref(
                    'yodoo_apps_database.yodoo_serie__17_0').id,
                'scan': True,
            },
        ])

    def _make_running_parent(self):
        task = self.Task.create_task(
            'yodoo_apps_website.source_sync', name='Sync Test Source',
            params={'source_id': self.source.id})
        task.sudo().action_assign(self.worker)
        task.sudo().action_start()
        return task

    def test_execute_creates_one_child_per_scannable_branch(self):
        task = self._make_running_parent()
        branch_ids = self.branches.ids

        with patch.object(
            type(self.source), '_g_task__prepare_sync',
            return_value=branch_ids,
        ):
            YodooSourceSyncTaskType().execute(self.env, task)

        children = task.child_ids
        self.assertEqual(len(children), len(branch_ids))
        for child in children:
            self.assertEqual(
                child.type_code, 'yodoo_apps_website.branch_sync')
            self.assertEqual(child.channel, BRANCH_CHANNEL)
        self.assertEqual(
            sorted(c.task_params['branch_id'] for c in children),
            sorted(branch_ids))
        for child in children:
            self.assertEqual(
                child.task_params['source_id'], self.source.id)

    def test_execute_puts_parent_in_waiting_state(self):
        task = self._make_running_parent()

        with patch.object(
            type(self.source), '_g_task__prepare_sync',
            return_value=self.branches.ids,
        ):
            YodooSourceSyncTaskType().execute(self.env, task)

        self.assertEqual(task.state, 'waiting')

    def test_execute_no_children_when_no_scannable_branches(self):
        """ Negative control: when there is nothing to scan, no child
            tasks are created and the source's last_time_synced is
            updated directly instead. """
        task = self._make_running_parent()
        synced_before = self.source.last_time_synced

        with patch.object(
            type(self.source), '_g_task__prepare_sync', return_value=[],
        ):
            result = YodooSourceSyncTaskType().execute(self.env, task)

        self.assertFalse(task.child_ids)
        self.assertEqual(result, {'status': 'done', 'branches': 0})
        self.assertNotEqual(self.source.last_time_synced, synced_before)
