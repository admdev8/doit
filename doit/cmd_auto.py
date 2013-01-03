"""starts a long-running process that whatches the file system and
automatically execute tasks when file dependencies change"""

import sys
from multiprocessing import Process

from .cmdparse import CmdParse
from .filewatch import FileModifyWatcher
from .cmd_base import DoitCmdBase
from .cmd_run import opt_verbosity, Run

opt_reporter = {'name':'reporter',
                 'short': None,
                 'long': None,
                 'type':str,
                 'default': 'executed-only',
                }


class Auto(DoitCmdBase):
    """the main process will never load tasks,
    delegates execution to a forked process.

    python caches imported modules,
    but using different process we can have dependencies on python
    modules making sure the newest module will be used.
    """

    doc_purpose = "automatically execute tasks when a dependency changes"
    doc_usage = "[TASK ...]"
    doc_description = None

    cmd_options = (opt_verbosity, opt_reporter)

    @staticmethod
    def _find_file_deps(tasks, sel_tasks):
        """find all file deps
        @param tasks (dict)
        @param sel_tasks(list - str)
        """
        deps = set()
        processed = set() # str - task name
        to_process = set(sel_tasks) # str - task name
        # get initial task
        while to_process:
            task = tasks.get(to_process.pop())
            processed.add(task.name)
            for task_dep in task.task_dep + task.setup_tasks:
                if (task_dep not in processed) and (task_dep not in to_process):
                    to_process.add(task_dep)
            deps.update(task.file_dep)
        return deps


    def run_watch(self, params, args):
        """Run tasks and wait for file system event

        This method is executed in a forked process.
        The process is terminated after a single event.
        """
        # execute tasks using Run Command
        ar = Run(task_loader=self._loader, dep_file=self.dep_file)
        params.add_defaults(CmdParse(ar.options).parse([])[0])
        result = ar.execute(params, args)

        # get list of files to watch on file system
        watch_files = self._find_file_deps(ar.control.tasks,
                                           ar.control.selected_tasks)

        # set event handler. just terminate process.
        class DoitAutoRun(FileModifyWatcher):
            def handle_event(self, event):
                print "FS EVENT -> ", event
                sys.exit(result)
        file_watcher = DoitAutoRun(watch_files)


        # FIXME events while tasks are running gonna be lost.
        # Check for timestamp changes since run started,
        # if no change: watch & wait
        # else: restart straight away

        # kick start watching process
        file_watcher.loop()


    def execute(self, params, args):
        """loop executing tasks until process is interrupted"""
        while True:
            try:
                p = Process(target=self.run_watch, args=(params, args))
                p.start()
                p.join()
            except KeyboardInterrupt:
                return 0
