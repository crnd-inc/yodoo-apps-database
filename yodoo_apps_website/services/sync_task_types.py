import logging

from odoo import fields

from odoo.addons.generic_task_queue import AbstractTaskType

_logger = logging.getLogger(__name__)

BRANCH_CHANNEL = 'yodoo_sync_branch'


class YodooSourceSyncTaskType(AbstractTaskType):
    """ Top-level task: connect to git, discover branches, spawn one
        child task per scannable branch, then aggregate on completion.
    """
    _name = 'yodoo_apps_website.source_sync'
    _notify_on_completion = True
    _retry_policy = 'non_retriable'

    def execute(self, env, task):
        source_id = task.task_params['source_id']
        branch_names = task.task_params.get('branch_names')
        source = env['yodoo.git.source'].browse(source_id).sudo()
        if not source.exists():
            return {'status': 'error', 'reason': 'source_missing'}

        scannable_ids = source._g_task__prepare_sync(branch_names)
        if not scannable_ids:
            source.write({'last_time_synced': fields.Datetime.now()})
            return {'status': 'done', 'branches': 0}

        children_params = [
            {'source_id': source_id, 'branch_id': bid}
            for bid in scannable_ids
        ]
        env['generic.task.queue.task'].sudo().create_children(
            task,
            type_code='yodoo_apps_website.branch_sync',
            params_list=children_params,
            channel=BRANCH_CHANNEL,
        )
        task.action_wait_children()
        return None

    def on_child_done(self, env, parent_task, child_task):
        done_children = len(parent_task.child_ids.filtered(
            lambda c: c.state in ('done', 'failed', 'cancelled')))
        total = len(parent_task.child_ids)
        if total:
            parent_task.update_progress(int(95 * done_children / total))

    def on_all_children_done(self, env, parent_task):
        source_id = parent_task.task_params['source_id']
        source = env['yodoo.git.source'].browse(source_id).sudo()
        if not source.exists():
            return {'status': 'error', 'reason': 'source_missing'}

        try:
            source._g_task__finalize_sync()
        except Exception as exc:
            _logger.warning(
                'Finalize sync failed for source %s: %s',
                source.name, exc, exc_info=True)

        children = parent_task.child_ids
        return {
            'branches_total': len(children),
            'branches_done': len(children.filtered(
                lambda c: c.state == 'done')),
            'branches_failed': len(children.filtered(
                lambda c: c.state == 'failed')),
            'last_time_synced': (
                source.last_time_synced
                and source.last_time_synced.isoformat()),
        }


class YodooBranchSyncTaskType(AbstractTaskType):
    """ Child task: sync modules + fetch descriptions for one branch. """
    _name = 'yodoo_apps_website.branch_sync'
    _retry_policy = 'retriable'
    _max_retries = 2
    _retry_delays = 'exponential'

    def execute(self, env, task):
        source_id = task.task_params['source_id']
        branch_id = task.task_params['branch_id']
        source = env['yodoo.git.source'].browse(source_id).sudo()
        branch = env['yodoo.git.source.branch'].browse(branch_id).sudo()
        if not source.exists() or not branch.exists():
            return {'skipped': True, 'reason': 'missing'}
        if not branch.scan:
            return {'skipped': True, 'reason': 'scan_disabled'}
        if task.is_cancelled():
            return {'skipped': True, 'reason': 'cancelled'}

        source._g_task__sync_one_branch(branch)
        return {
            'source': source.name,
            'branch': branch.name,
            'modules': len(branch.git_module_ids),
        }
