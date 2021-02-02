"""
Tests for the SVN state
"""

import os
import shutil
import socket

from tests.support.case import ModuleCase
from tests.support.helpers import slowTest
from tests.support.mixins import SaltReturnAssertsMixin
from tests.support.runtests import RUNTIME_VARS


class SvnTest(ModuleCase, SaltReturnAssertsMixin):
    """
    Validate the svn state
    """

    def setUp(self):
        super().setUp()

        if not self.run_function("cmd.has_exec", ["svn"]):
            self.skipTest("The executable 'svn' is not available.")

        self.__domain = "svn.apache.org"
        try:
            if hasattr(socket, "setdefaulttimeout"):
                # 10 second dns timeout
                socket.setdefaulttimeout(10)
            socket.gethostbyname(self.__domain)
        except OSError:
            msg = "error resolving {0}, possible network issue?"
            self.skipTest(msg.format(self.__domain))

        self.target = os.path.join(RUNTIME_VARS.TMP, "apache_http_test_repo")
        self.name = "http://{}/repos/asf/httpd/httpd/trunk/test/".format(self.__domain)
        self.new_rev = "1456987"

    def tearDown(self):
        shutil.rmtree(self.target, ignore_errors=True)
        # Reset the dns timeout after the test is over
        socket.setdefaulttimeout(None)

    @slowTest
    def test_latest(self):
        """
        svn.latest
        """
        ret = self.run_state(
            "svn.latest", name=self.name, rev=self.new_rev, target=self.target,
        )
        self.assertSaltTrueReturn(ret)
        self.assertTrue(os.path.isdir(os.path.join(self.target, ".svn")))
        self.assertSaltStateChangesEqual(ret, self.name, keys=["new"])
        self.assertSaltStateChangesEqual(ret, self.new_rev, keys=["revision"])

    @slowTest
    def test_latest_failure(self):
        """
        svn.latest
        """
        ret = self.run_state(
            "svn.latest",
            name="https://youSpelledApacheWrong.com/repo/asf/httpd/trunk/",
            rev=self.new_rev,
            target=self.target,
        )
        self.assertSaltFalseReturn(ret)
        self.assertFalse(os.path.isdir(os.path.join(self.target, ".svn")))

    @slowTest
    def test_latest_empty_dir(self):
        """
        svn.latest
        """
        if not os.path.isdir(self.target):
            os.mkdir(self.target)
        ret = self.run_state(
            "svn.latest", name=self.name, rev=self.new_rev, target=self.target,
        )
        self.assertSaltTrueReturn(ret)
        self.assertTrue(os.path.isdir(os.path.join(self.target, ".svn")))

    def no_test_latest_existing_repo(self):
        """
        svn.latest against existing repository
        """
        current_rev = "1442865"
        cwd, basename = os.path.split(self.target)
        opts = ("-r", current_rev)

        out = self.run_function(
            "svn.checkout", [cwd, self.name, basename, None, None, opts]
        )
        assert out

        ret = self.run_state(
            "svn.latest", name=self.name, rev=self.new_rev, target=self.target,
        )
        self.assertSaltTrueReturn(ret)
        self.assertSaltStateChangesEqual(
            ret, "{} => {}".format(current_rev, self.new_rev), keys=["revision"]
        )
        self.assertTrue(os.path.isdir(os.path.join(self.target, ".svn")))

    def no_test_latest_existing_repo_no_rev_change(self):
        """
        svn.latest against existing repository
        """
        current_rev = self.new_rev
        cwd, basename = os.path.split(self.target)
        opts = ("-r", current_rev)
        out = self.run_function(
            "svn.checkout", [cwd, self.name, basename, None, None, opts]
        )
        assert out
        ret = self.run_state(
            "svn.latest", name=self.name, rev=self.new_rev, target=self.target,
        )
        self.assertSaltTrueReturn(ret)
        self.assertSaltStateChangesEqual(ret, {})
        self.assertTrue(os.path.isdir(os.path.join(self.target, ".svn")))
