import unittest
import sys
from io import StringIO
from contextlib import contextmanager
from borg import Borg, ChildShare, ChildNotShare
from null_object import NullObject
from observer import Publisher, Subscriber
from proxy import Proxy, Implementation
from singleton import Singleton, Child, GrandChild
from strategy import Strategy, execute_replacement1, execute_replacement2


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestBorg(unittest.TestCase):

    def test_two_borgs_have_different_identity(self):
        a = Borg('Mark')
        b = Borg('Luke')
        self.assertIsNot(a, b)

    def test_two_borgs_share_common_state(self):
        a = Borg('Mark')
        b = Borg('Luke')
        self.assertEqual(a.state, b.state)

    def test_borg_and_childshare_share_common_state(self):
        a = Borg('Mark')
        c = ChildShare('Paul', color='red')
        self.assertEqual(a.state, c.state)

    def test_borg_and_childnotshare_do_not_share_common_state(self):
        a = Borg('Mark')
        d = ChildNotShare('Andrew', age=5)
        self.assertNotEqual(a.state, d.state)

    def test_two_childnotshare_share_common_state(self):
        d = ChildNotShare('Andrew', age=5)
        e = ChildNotShare('Tom', age=7)
        self.assertEqual(d.state, e.state)

    def test_update_state(self):
        a = Borg('Mark')
        c = ChildShare('Paul', color='red')
        self.assertIn('color', a.state)
        d = ChildNotShare('Andrew', age=5)
        a.name = 'James'
        self.assertEqual(a.name, c.name)
        self.assertNotEqual(a.name, d.name)


class TestNullObject(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.null = NullObject(name='Bob')

    def test_null_object_is_null(self):
        self.assertTrue(self.null.is_null)

    def test_null_has_no_name(self):
        self.assertIsNot(self.null.name, 'Bob')

    def test_repr_of_null_object(self):
        self.assertEqual(repr(self.null), '<Null>')

    def test_do_stuff_does_nothing(self):
        self.assertIsNone(self.null.do_stuff())

    def test_get_stuff_gets_nothing(self):
        self.assertIsNone(self.null.get_stuff())


class TestObserver(unittest.TestCase):

    def setUp(self):
        self.newsletters = ['Tech', 'Travel', 'Fashion']
        self.pub = Publisher(self.newsletters)
        subscribers = [('s0', 'Tom'), ('s1', 'Sara')]
        for sub, name in subscribers:
            setattr(self, sub, Subscriber(name))

        # before each test case, set some subscriptions
        self.pub.register('Tech', self.s0)
        self.pub.register('Travel', self.s0)
        self.pub.register('Travel', self.s1)

    def tearDown(self):
        # after each test case, reset the subscriptions
        for newsletter in self.newsletters:
            if self.s0 in self.pub.subscriptions[newsletter]:
                self.pub.unregister(newsletter, self.s0)
            if self.s1 in self.pub.subscriptions[newsletter]:
                self.pub.unregister(newsletter, self.s1)

    def test_register_subscriber(self):
        john = Subscriber('John')
        self.pub.register(newsletter='Tech', who=john)
        self.assertEqual(self.pub.subscriptions['Tech'][john], john.receive)
        self.pub.unregister(newsletter='Tech', who=john)  # cleanup

    def test_unregister_subscriber(self):
        self.assertIn(self.s0, self.pub.get_subscriptions('Tech'))
        self.pub.unregister('Tech', self.s0)
        self.assertNotIn(self.s0, self.pub.get_subscriptions('Tech'))

    def test_dispatch_newsletter(self):
        with captured_output() as (out, err):
            self.pub.dispatch(
                newsletter='Tech', message='Tech Newsletter num 1')
        output = out.getvalue().strip()
        self.assertEqual(output, 'Tom received: Tech Newsletter num 1')

    def test_get_subscription_without_subscribers(self):
        self.assertEqual(self.pub.get_subscriptions('Fashion'), {})

    def test_get_subscription_with_subscribers(self):
        self.assertIn(self.s0, self.pub.get_subscriptions('Tech'))

    def test_add_newsletter(self):
        self.assertNotIn('Videogames', self.pub.subscriptions.keys())
        self.pub.add_newsletter('Videogames')
        self.assertIn('Videogames', self.pub.subscriptions.keys())

    def test_subscription_does_not_exist(self):
        with self.assertRaises(KeyError):
            self.pub.subscriptions['Videogames']


class TestProxy(unittest.TestCase):

    def test_load_real_or_cached_object(self):
        p1 = Proxy(Implementation('RealObject1'))

        # the first time we call do_stuff we need to load the real object
        with captured_output() as (out, err):
            p1.do_stuff()
        output = out.getvalue().strip()
        self.assertEqual(output, 'load RealObject1\ndo stuff on RealObject1')

        # after that, loading is unnecessary (we use the cached object)
        with captured_output() as (out, err):
            p1.do_stuff()
        output = out.getvalue().strip()
        self.assertEqual(output, 'do stuff on RealObject1')


class TestSingleton(unittest.TestCase):

    def test_two_singletons_have_same_identity(self):
        s1 = Singleton('Sam')
        s2 = Singleton('Tom')
        self.assertIs(s1, s2)

    def test_singleton_and_child_have_different_identity(self):
        s1 = Singleton('Sam')
        c1 = Child('John')
        self.assertIsNot(s1, c1)

    def test_two_children_have_same_identity(self):
        c1 = Child('John')
        c2 = Child('Andy')
        self.assertIs(c1, c2)

    def test_child_and_grandchild_have_different_identity(self):
        c1 = Child('John')
        g1 = GrandChild('Bob')
        self.assertIsNot(c1, g1)


class TestStrategy(unittest.TestCase):

    def test_default_strategy(self):
        self.assertEqual(Strategy().name, 'Strategy_default')

    def test_replacement_strategy_one(self):
        self.assertEqual(Strategy(execute_replacement1).name,
                         'Strategy_execute_replacement1')

    def test_replacement_strategy_two(self):
        self.assertEqual(Strategy(execute_replacement2).name,
                         'Strategy_execute_replacement2')


if __name__ == '__main__':
    unittest.main()
