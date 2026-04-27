from odoo.addons.generic_task_queue.service.task_queue_service import (
    TaskQueueService,
)


class YodooSyncBranchService(TaskQueueService):
    """ Dedicated worker pool for branch-level sync tasks.

        Branches of the same source share yodoo.module records (a module
        usually exists on several branches). Running them in parallel
        causes psycopg2 SerializationFailure on concurrent
        create_or_update_module / create_or_update_version. We keep
        _max_parallel_jobs = 1 to serialize branch processing.

        Cross-source parallelism still happens at the parent level:
        the default worker enqueues children for several sources, and
        this worker drains them one at a time, but each parent is
        blocked only on its own children, so multiple parents sit in
        `waiting` simultaneously while their branches stream through.
    """
    _name = 'yodoo_apps_website.sync_branch_service'
    _require_module = 'yodoo_apps_website'

    _task_types = ['yodoo_apps_website.branch_sync']
    _channels = ['yodoo_sync_branch']
    _max_parallel_jobs = 1
