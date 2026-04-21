from odoo.addons.generic_task_queue.service.task_queue_service import (
    TaskQueueService,
)


class YodooSyncBranchService(TaskQueueService):
    """ Dedicated worker pool for branch-level sync tasks.

        Caps concurrency at 3 to stay within git API rate-limits.
        The top-level source-sync task uses the default channel and
        runs on the default worker.
    """
    _name = 'yodoo_apps_website.sync_branch_service'
    _require_module = 'yodoo_apps_website'

    _task_types = ['yodoo_apps_website.branch_sync']
    _channels = ['yodoo_sync_branch']
    _max_parallel_jobs = 3
