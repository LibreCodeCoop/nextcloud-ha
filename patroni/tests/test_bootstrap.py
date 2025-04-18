import os
import sys

from unittest.mock import Mock, patch, PropertyMock

from patroni.async_executor import CriticalTask
from patroni.collections import CaseInsensitiveDict
from patroni.postgresql import Postgresql
from patroni.postgresql.bootstrap import Bootstrap
from patroni.postgresql.cancellable import CancellableSubprocess
from patroni.postgresql.config import ConfigHandler, get_param_diff
from patroni.postgresql.misc import PostgresqlState

from . import BaseTestPostgresql, mock_available_gucs, psycopg_connect


@patch('subprocess.call', Mock(return_value=0))
@patch('subprocess.check_output', Mock(return_value=b"postgres (PostgreSQL) 12.1"))
@patch('patroni.psycopg.connect', psycopg_connect)
@patch('os.rename', Mock())
@patch.object(Postgresql, 'available_gucs', mock_available_gucs)
class TestBootstrap(BaseTestPostgresql):

    @patch('patroni.postgresql.CallbackExecutor', Mock())
    def setUp(self):
        super(TestBootstrap, self).setUp()
        self.b = self.p.bootstrap

    @patch('time.sleep', Mock())
    @patch.object(CancellableSubprocess, 'call')
    @patch.object(Postgresql, 'remove_data_directory', Mock(return_value=True))
    @patch.object(Postgresql, 'data_directory_empty', Mock(return_value=False))
    @patch.object(Bootstrap, '_post_restore', Mock(side_effect=OSError))
    def test_create_replica(self, mock_cancellable_subprocess_call):
        self.p.config._config['create_replica_methods'] = ['pgBackRest']
        self.p.config._config['pgBackRest'] = {'command': 'pgBackRest', 'keep_data': True, 'no_params': True}
        mock_cancellable_subprocess_call.return_value = 0
        self.assertEqual(self.b.create_replica(self.leader), 0)

        self.p.config._config['create_replica_methods'] = ['basebackup']
        self.p.config._config['basebackup'] = [{'max_rate': '100M'}, 'no-sync']
        self.assertEqual(self.b.create_replica(self.leader), 0)

        self.p.config._config['basebackup'] = [{'max_rate': '100M', 'compress': '9'}]
        with patch('patroni.postgresql.bootstrap.logger.error', new_callable=Mock()) as mock_logger:
            self.b.create_replica(self.leader)
            mock_logger.assert_called_once()
            self.assertTrue("only one key-value is allowed and value should be a string" in mock_logger.call_args[0][0],
                            "not matching {0}".format(mock_logger.call_args[0][0]))

        self.p.config._config['basebackup'] = [42]
        with patch('patroni.postgresql.bootstrap.logger.error', new_callable=Mock()) as mock_logger:
            self.b.create_replica(self.leader)
            mock_logger.assert_called_once()
            self.assertTrue("value should be string value or a single key-value pair" in mock_logger.call_args[0][0],
                            "not matching {0}".format(mock_logger.call_args[0][0]))

        self.p.config._config['basebackup'] = {"foo": "bar"}
        self.assertEqual(self.b.create_replica(self.leader), 0)

        self.p.config._config['create_replica_methods'] = ['wale', 'basebackup']
        del self.p.config._config['basebackup']
        mock_cancellable_subprocess_call.return_value = 1
        self.assertEqual(self.b.create_replica(self.leader), 1)

        mock_cancellable_subprocess_call.side_effect = Exception('foo')
        self.assertEqual(self.b.create_replica(self.leader), 1)

        mock_cancellable_subprocess_call.side_effect = [1, 0]
        self.assertEqual(self.b.create_replica(self.leader), 0)

        mock_cancellable_subprocess_call.side_effect = [Exception(), 0]
        self.assertEqual(self.b.create_replica(self.leader), 0)

        self.p.cancellable.cancel()
        self.assertEqual(self.b.create_replica(self.leader), 1)

    @patch('time.sleep', Mock())
    @patch.object(CancellableSubprocess, 'call')
    @patch.object(Postgresql, 'remove_data_directory', Mock(return_value=True))
    @patch.object(Bootstrap, '_post_restore', Mock(side_effect=OSError))
    def test_create_replica_old_format(self, mock_cancellable_subprocess_call):
        """ The same test as before but with old 'create_replica_method'
            to test backward compatibility
        """
        self.p.config._config['create_replica_method'] = ['wale', 'basebackup']
        self.p.config._config['wale'] = {'command': 'foo'}
        mock_cancellable_subprocess_call.return_value = 0
        self.assertEqual(self.b.create_replica(self.leader), 0)
        del self.p.config._config['wale']
        self.assertEqual(self.b.create_replica(self.leader), 0)

        self.p.config._config['create_replica_method'] = ['wale']
        mock_cancellable_subprocess_call.return_value = 1
        self.assertEqual(self.b.create_replica(self.leader), 1)

    @patch.object(CancellableSubprocess, 'call', Mock(return_value=0))
    @patch.object(Postgresql, 'data_directory_empty', Mock(return_value=True))
    def test_basebackup(self):
        with patch('patroni.postgresql.bootstrap.logger.debug') as mock_debug:
            self.p.cancellable.cancel()
            self.b.basebackup("", None, {'foo': 'bar'})
            mock_debug.assert_not_called()

            self.p.cancellable.reset_is_cancelled()
            self.b.basebackup("", None, {'foo': 'bar'})
            mock_debug.assert_called_with(
                'calling: %r',
                ['pg_basebackup', f'--pgdata={self.p.data_dir}', '-X', 'stream', '--dbname=', '--foo=bar'],
            )

    def test__initdb(self):
        self.assertRaises(Exception, self.b.bootstrap, {'initdb': [{'pgdata': 'bar'}]})
        self.assertRaises(Exception, self.b.bootstrap, {'initdb': [{'foo': 'bar', 1: 2}]})
        self.assertRaises(Exception, self.b.bootstrap, {'initdb': [1]})
        self.assertRaises(Exception, self.b.bootstrap, {'initdb': 1})

    def test__process_user_options(self):
        def error_handler(msg):
            raise Exception(msg)

        self.assertEqual(self.b.process_user_options('initdb', ['string'], (), error_handler), ['--string'])
        self.assertEqual(
            self.b.process_user_options(
                'initdb',
                [{'key': 'value'}],
                (), error_handler
            ),
            ['--key=value'])
        if sys.platform != 'win32':
            self.assertEqual(
                self.b.process_user_options(
                    'initdb',
                    [{'key': 'value with spaces'}],
                    (), error_handler
                ),
                ["--key=value with spaces"])
            self.assertEqual(
                self.b.process_user_options(
                    'initdb',
                    [{'key': "'value with spaces'"}],
                    (), error_handler
                ),
                ["--key=value with spaces"])
            self.assertEqual(
                self.b.process_user_options(
                    'initdb',
                    {'key': 'value with spaces'},
                    (), error_handler
                ),
                ["--key=value with spaces"])
            self.assertEqual(
                self.b.process_user_options(
                    'initdb',
                    {'key': "'value with spaces'"},
                    (), error_handler
                ),
                ["--key=value with spaces"])
            # not allowed options in list of dicts/strs are filtered out
            self.assertEqual(
                self.b.process_user_options(
                    'pg_basebackup',
                    [{'checkpoint': 'fast'}, {'dbname': 'dbname=postgres'}, 'gzip', {'label': 'standby'}, 'verbose'],
                    ('dbname', 'verbose'),
                    print
                ),
                ['--checkpoint=fast', '--gzip', '--label=standby'],
            )

    @patch.object(CancellableSubprocess, 'call', Mock())
    @patch.object(Postgresql, 'is_running', Mock(return_value=True))
    @patch.object(Postgresql, 'data_directory_empty', Mock(return_value=False))
    @patch.object(Postgresql, 'controldata', Mock(return_value={'max_connections setting': 100,
                                                                'max_prepared_xacts setting': 0,
                                                                'max_locks_per_xact setting': 64}))
    def test_bootstrap(self):
        with patch('subprocess.call', Mock(return_value=1)):
            self.assertFalse(self.b.bootstrap({}))

        config = {}

        with patch.object(Postgresql, 'is_running', Mock(return_value=False)), \
                patch.object(Postgresql, 'get_major_version', Mock(return_value=140000)), \
                patch('multiprocessing.Process', Mock(side_effect=Exception)), \
                patch('multiprocessing.get_context', Mock(side_effect=Exception), create=True):
            self.assertRaises(Exception, self.b.bootstrap, config)
        with open(os.path.join(self.p.data_dir, 'pg_hba.conf')) as f:
            lines = f.readlines()
            self.assertTrue('host all all 0.0.0.0/0 md5\n' in lines)

        self.p.config._config.pop('pg_hba')
        config.update({'post_init': '/bin/false',
                       'pg_hba': ['host replication replicator 127.0.0.1/32 md5',
                                  'hostssl all all 0.0.0.0/0 md5',
                                  'host all all 0.0.0.0/0 md5']})
        self.b.bootstrap(config)
        with open(os.path.join(self.p.data_dir, 'pg_hba.conf')) as f:
            lines = f.readlines()
            self.assertTrue('host replication replicator 127.0.0.1/32 md5\n' in lines)

    @patch.object(CancellableSubprocess, 'call')
    @patch.object(Postgresql, 'get_major_version', Mock(return_value=90600))
    @patch.object(Postgresql, 'controldata', Mock(return_value={'Database cluster state': 'in production'}))
    def test_custom_bootstrap(self, mock_cancellable_subprocess_call):
        self.p.config._config.pop('pg_hba')
        config = {'method': 'foo', 'foo': {'command': 'bar --arg1=val1'}}

        mock_cancellable_subprocess_call.return_value = 1
        self.assertFalse(self.b.bootstrap(config))
        self.assertEqual(mock_cancellable_subprocess_call.call_args_list[0][0][0],
                         ['bar', '--arg1=val1', '--scope=batman', '--datadir=' + os.path.join('data', 'test0')])

        mock_cancellable_subprocess_call.reset_mock()
        config['foo']['no_params'] = 1
        self.assertFalse(self.b.bootstrap(config))
        self.assertEqual(mock_cancellable_subprocess_call.call_args_list[0][0][0], ['bar', '--arg1=val1'])

        mock_cancellable_subprocess_call.return_value = 0
        with patch('multiprocessing.Process', Mock(side_effect=Exception("42"))), \
                patch('multiprocessing.get_context', Mock(side_effect=Exception("42")), create=True), \
                patch('os.path.isfile', Mock(return_value=True)), \
                patch('os.unlink', Mock()), \
                patch.object(ConfigHandler, 'save_configuration_files', Mock()), \
                patch.object(ConfigHandler, 'restore_configuration_files', Mock()), \
                patch.object(ConfigHandler, 'write_recovery_conf', Mock()):
            with self.assertRaises(Exception) as e:
                self.b.bootstrap(config)
            self.assertEqual(str(e.exception), '42')

            config['foo']['recovery_conf'] = {'foo': 'bar'}

            with self.assertRaises(Exception) as e:
                self.b.bootstrap(config)
            self.assertEqual(str(e.exception), '42')

        mock_cancellable_subprocess_call.side_effect = Exception
        self.assertFalse(self.b.bootstrap(config))

    @patch('time.sleep', Mock())
    @patch('os.unlink', Mock())
    @patch('shutil.copy', Mock())
    @patch('os.path.isfile', Mock(return_value=True))
    @patch('patroni.postgresql.bootstrap.quote_ident', Mock())
    @patch.object(Bootstrap, 'call_post_bootstrap', Mock(return_value=True))
    @patch.object(Bootstrap, '_custom_bootstrap', Mock(return_value=True))
    @patch.object(Postgresql, 'start', Mock(return_value=True))
    @patch.object(Postgresql, 'get_major_version', Mock(return_value=110000))
    def test_post_bootstrap(self):
        config = {'method': 'foo', 'foo': {'command': 'bar'}}
        self.b.bootstrap(config)

        task = CriticalTask()
        with patch.object(Bootstrap, 'create_or_update_role', Mock(side_effect=Exception)):
            self.b.post_bootstrap({}, task)
            self.assertFalse(task.result)

        self.p.config._config.pop('pg_hba')
        with patch('patroni.postgresql.bootstrap.logger.error', new_callable=Mock()) as mock_logger:
            self.b.post_bootstrap({'users': 1}, task)
            self.assertEqual(mock_logger.call_args_list[0][0][0],
                             'User creation is not be supported starting from v4.0.0. '
                             'Please use "bootstrap.post_bootstrap" script to create users.')
            self.assertTrue(task.result)

        self.b.bootstrap(config)
        with patch.object(Postgresql, 'pending_restart_reason',
                          PropertyMock(CaseInsensitiveDict({'max_connections': get_param_diff('200', '100')}))), \
             patch.object(Postgresql, 'restart', Mock()) as mock_restart:
            self.b.post_bootstrap({}, task)
            mock_restart.assert_called_once()

        self.b.bootstrap(config)
        self.p.set_state(PostgresqlState.STOPPED)
        self.p.reload_config({'authentication': {'superuser': {'username': 'p', 'password': 'p'},
                                                 'replication': {'username': 'r', 'password': 'r'},
                                                 'rewind': {'username': 'rw', 'password': 'rw'}},
                              'listen': '*', 'retry_timeout': 10,
                              'parameters': {'wal_level': '', 'hba_file': 'foo', 'max_prepared_transactions': 10}})
        with patch.object(Postgresql, 'major_version', PropertyMock(return_value=110000)), \
                patch.object(Postgresql, 'restart', Mock()) as mock_restart:
            self.b.post_bootstrap({}, task)
            mock_restart.assert_called_once()

    @patch.object(CancellableSubprocess, 'call')
    def test_call_post_bootstrap(self, mock_cancellable_subprocess_call):
        mock_cancellable_subprocess_call.return_value = 1
        self.assertFalse(self.b.call_post_bootstrap({'post_init': '/bin/false'}))

        mock_cancellable_subprocess_call.return_value = 0
        self.p.connection_pool._conn_kwargs.pop('user')
        self.assertTrue(self.b.call_post_bootstrap({'post_init': '/bin/false'}))
        mock_cancellable_subprocess_call.assert_called()
        args, kwargs = mock_cancellable_subprocess_call.call_args
        self.assertTrue('PGPASSFILE' in kwargs['env'])
        self.assertEqual(args[0], ['/bin/false', 'dbname=postgres host=/tmp port=5432'])

        mock_cancellable_subprocess_call.reset_mock()
        self.p.connection_pool._conn_kwargs.pop('host')
        self.assertTrue(self.b.call_post_bootstrap({'post_init': '/bin/false'}))
        mock_cancellable_subprocess_call.assert_called()
        self.assertEqual(mock_cancellable_subprocess_call.call_args[0][0], ['/bin/false', 'dbname=postgres port=5432'])

        mock_cancellable_subprocess_call.side_effect = OSError
        self.assertFalse(self.b.call_post_bootstrap({'post_init': '/bin/false'}))

    @patch('os.path.exists', Mock(return_value=True))
    @patch('os.unlink', Mock())
    @patch.object(Bootstrap, 'create_replica', Mock(return_value=0))
    def test_clone(self):
        self.b.clone(self.leader)
