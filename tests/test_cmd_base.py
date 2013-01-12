import pytest

from doit.cmdparse import CmdParseError, CmdOption
from doit.task import Task
from doit.cmd_base import Command, DoitCmdBase
from doit.cmd_base import ModuleTaskLoader, DodoTaskLoader
from doit.cmd_base import tasks_and_deps_iter, subtasks_iter


opt_bool = {'name': 'flag',
            'short':'f',
            'long': 'flag',
            'inverse':'no-flag',
            'type': bool,
            'default': False,
            'help': 'help for opt1'}

opt_rare = {'name': 'rare',
            'long': 'rare-bool',
            'type': bool,
            'default': False,
            'help': 'help for opt2'}

opt_int = {'name': 'num',
           'short':'n',
           'long': 'number',
           'type': int,
           'default': 5,
           'help': 'help for opt3'}

opt_no = {'name': 'no',
          'short':'',
          'long': '',
          'type': int,
          'default': 5,
          'help': 'user cant modify me'}



class SampleCmd(Command):
    doc_purpose = 'PURPOSE'
    doc_usage = 'USAGE'
    doc_description = 'DESCRIPTION'

    @staticmethod
    def execute(params, args):
        return params, args

    def set_options(self):
        options = [opt_bool, opt_rare, opt_int, opt_no]
        return [CmdOption(o) for o in options]

class TestCommand(object):

    @pytest.fixture
    def cmd(self, request):
        return SampleCmd()

    def test_help(self, cmd):
        text = cmd.help()
        assert 'PURPOSE' in text
        assert 'USAGE' in text
        assert 'DESCRIPTION' in text
        assert '-f' in text
        assert '--rare-bool' in text
        assert 'help for opt1' in text
        assert opt_no['name'] in [o.name for o in cmd.options]
        assert 'user cant modify me' not in text


    def test_call(self, cmd):
        params, args = cmd.parse_execute(['-n','7','ppp'])
        assert ['ppp'] == args
        assert 7 == params['num']

    def test_failCall(self, cmd):
        pytest.raises(CmdParseError, cmd.parse_execute, ['-x','35'])


class TestModuleTaskLoader(object):
    def test_load_tasks(self, cwd):
        cmd = Command()
        members = {'task_xxx1': lambda : {'actions':[]},
                   'task_no': 'strings are not tasks',
                   'blabla': lambda :None,
                   'DOIT_CONFIG': {'verbose': 2},
                   }
        loader = ModuleTaskLoader(members)
        task_list, config = loader.load_tasks(cmd, {}, [])
        assert ['xxx1'] == [t.name for t in task_list]
        assert {'verbose': 2} == config


class TestDodoTaskLoader(object):
    def test_load_tasks(self, cwd):
        cmd = Command()
        params = {'dodoFile': 'loader_sample.py',
                  'cwdPath': None,
                  'seek_file': False,
                  }
        loader = DodoTaskLoader()
        task_list, config = loader.load_tasks(cmd, params, [])
        assert ['xxx1', 'yyy2'] == [t.name for t in task_list]
        assert {'verbose': 2} == config



class TestDoitCmdBase(object):
    def test(self):
        class MyCmd(DoitCmdBase):
            doc_purpose = "fake for testing"
            doc_usage = "[TASK ...]"
            doc_description = None

            opt_my = {
                'name': 'my_opt',
                'short':'m',
                'long': 'mine',
                'type': str,
                'default': 'xxx',
                'help': "my option"
               }

            cmd_options = (opt_my,)

            def _execute(self, my_opt):
                return my_opt

        mycmd = MyCmd(DodoTaskLoader())
        assert 'min' == mycmd.parse_execute(['--mine', 'min'])



class TestTaskAndDepsIter(object):

    def test_dep_iter(self):
        tasks = {
            't1': Task("t1", [""] ),
            't2': Task("t2", [""], task_dep=['t1']),
            't3': Task("t3", [""], setup=['t1']),
            't4': Task("t4", [""], task_dep=['t3']),
            }
        def names(sel_tasks):
            return [t.name for t in tasks_and_deps_iter(tasks, sel_tasks)]

        assert ['t1'] == names(['t1'])
        assert ['t2', 't1'] == names(['t2'])
        assert ['t3', 't1'] == names(['t3'])
        assert ['t4', 't3', 't1'] == names(['t4'])


class TestSubtaskIter(object):

    def test_sub_iter(self):
        tasks = {
            't1': Task("t1", [""] ),
            't2': Task("t2", [""], task_dep=['t1', 't2:a', 't2:b']),
            't2:a': Task("t2:a", [""], is_subtask=True),
            't2:b': Task("t2:b", [""], is_subtask=True),
            }
        def names(task_name):
            return [t.name for t in subtasks_iter(tasks, tasks[task_name])]

        assert [] == names('t1')
        assert ['t2:a', 't2:b'] == names('t2')
