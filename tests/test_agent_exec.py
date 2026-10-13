import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('agent_exec', Path(__file__).parents[1] / 'tools/agent_exec.py')
agent_exec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_exec)


class AgentRoutingTests(unittest.TestCase):
    def test_roles_and_exception(self):
        self.assertEqual(agent_exec.route('qualification'), ('gpt-6-luna','medium'))
        self.assertEqual(agent_exec.route('quality_review','high','Complex conflicting evidence'), ('gpt-6-sol','high'))
        with self.assertRaises(ValueError): agent_exec.route('quality_review','high')
        with self.assertRaises(ValueError): agent_exec.route('discovery','medium','Reason')

    def test_explicit_flags_and_verified_actual_route(self):
        commands = []
        def run(command, **kwargs):
            commands.append((command,kwargs))
            output = '\n'.join(json.dumps(item) for item in (
                {'type':'thread.started','thread_id':'thread-test'},
                {'type':'item.completed','item':{'type':'agent_message','text':'ok'}},
                {'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':2}}))
            return SimpleNamespace(returncode=0,stdout=output)
        result = agent_exec.execute('qualification','Fictitious task',run=run,
                                    observe=lambda thread: ('gpt-6-luna','medium'))
        self.assertEqual(result['usage']['input_tokens'],10)
        self.assertEqual(result['model'],'gpt-6-luna')
        self.assertIn('-m',commands[0][0])
        self.assertIn('model_reasoning_effort="medium"',commands[0][0])
        self.assertEqual(commands[0][1]['input'],'Fictitious task')
        with self.assertRaisesRegex(ValueError,'differs'):
            agent_exec.execute('qualification','Task',run=run,
                               observe=lambda thread: ('gpt-6-sol','medium'))

        recorded = []
        agent_exec.execute('qualification','Task',job='job-1',worker='worker-1',run=run,
                           observe=lambda thread: ('gpt-6-luna','medium'),
                           record=lambda *values: recorded.append(values))
        self.assertEqual(recorded[0][:5], ('job-1','worker-1','thread-test','gpt-6-luna','medium'))
        with self.assertRaisesRegex(ValueError,'together'):
            agent_exec.execute('qualification','Task',job='job-1',run=run)


if __name__ == '__main__': unittest.main()
