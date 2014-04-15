# Copyright (C) 2012-2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from __future__ import absolute_import
from tests import support

import dnf.comps
import dnf.util
import operator
import warnings


class EmptyPersistorTest(support.ResultTestCase):
    """Test group operations with empty persistor."""

    def setUp(self):
        self.base = support.MockBase('main')
        self.base.read_mock_comps_empty_prst()
        self.base.init_sack()

    def test_group_install_exclude(self):
        comps = self.base.comps
        grp = comps.group_by_pattern('somerset')
        cnt = self.base.group_install(grp, ('optional',), exclude=('lotus',))
        self.assertEqual(cnt, 0)

    def test_add_comps_trans(self):
        trans = dnf.comps.TransactionBunch()
        trans.install.add('trampoline')
        self.assertGreater(self.base._add_comps_trans(trans), 0)
        (installed, removed) = self.installed_removed(self.base)
        self.assertItemsEqual(map(str, installed), ('trampoline-2.1-1.noarch',))
        self.assertEmpty(removed)

        trans = dnf.comps.TransactionBunch()
        trans.install.add('waltz')
        self.assertEqual(self.base._add_comps_trans(trans), 0)

class PresetPersistorTest(support.ResultTestCase):
    """Test group operations with some data in the persistor."""

    def setUp(self):
        self.base = support.MockBase("main")
        self.base.read_mock_comps(support.COMPS_PATH)
        self.base.init_sack()

    def test_environment_list(self):
        env_inst, env_avail = self.base._environment_list(['sugar*'])
        self.assertLength(env_inst, 1)
        self.assertLength(env_avail, 0)
        self.assertEqual(env_inst[0].name, 'Sugar Desktop Environment')

    def test_environment_remove(self):
        comps = self.base.comps
        env = comps.environment_by_pattern("sugar-desktop-environment")
        self.assertGreater(self.base.environment_remove(env), 0)
        prst = self.base.group_persistor
        p_env = prst.environment(env.id)
        self.assertFalse(p_env.installed)
        peppers = prst.group('Peppers')
        somerset = prst.group('somerset')
        self.assertFalse(peppers.installed)
        self.assertFalse(somerset.installed)

    def test_install(self):
        comps = self.base.comps
        grp = dnf.util.first(comps.groups_by_pattern("Solid Ground"))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertEqual(self.base.select_group(grp), 1)
        inst, removed = self.installed_removed(self.base)
        self.assertItemsEqual([pkg.name for pkg in inst], ("trampoline",))
        self.assertLength(removed, 0)

    def test_group_install(self):
        prst = self.base.group_persistor
        grp = self.base.comps.group_by_pattern('Base')
        p_grp = prst.group('base')
        self.assertFalse(p_grp.installed)

        self.assertEqual(self.base.group_install(grp, ('mandatory',)), 2)
        inst, removed = self.installed_removed(self.base)
        self.assertEmpty(inst)
        self.assertEmpty(removed)
        self.assertTrue(p_grp.installed)

    def test_group_remove(self):
        prst = self.base.group_persistor
        grp = self.base.comps.group_by_pattern('somerset')
        p_grp = prst.group('somerset')

        self.assertGreater(self.base.group_remove(grp), 0)
        inst, removed = self.installed_removed(self.base)
        self.assertEmpty(inst)
        self.assertItemsEqual([pkg.name for pkg in removed], ('pepper',))
        self.assertFalse(p_grp.installed)


class EnvironmentInstallTest(support.ResultTestCase):
    def setUp(self):
        """Set up a test where sugar is considered not installed."""
        self.base = support.MockBase("main")
        self.base.init_sack()
        self.base.read_mock_comps(support.COMPS_PATH)
        self.prst = self.base.group_persistor
        p_env = self.prst.environment('sugar-desktop-environment')
        p_env.pkg_types = 0
        p_env.grp_types = 0
        del p_env.full_list[:]
        p_grp = self.prst.group('somerset')
        p_grp.pkg_types = 0
        del p_grp.full_list[:]

    def test_environment_install(self):
        comps = self.base.comps
        env = comps.environment_by_pattern("sugar-desktop-environment")
        self.base.environment_install(env, ('mandatory',))
        installed, _ = self.installed_removed(self.base)
        self.assertItemsEqual(map(operator.attrgetter('name'), installed),
                              ('trampoline',))

        p_env = self.prst.environment('sugar-desktop-environment')
        self.assertItemsEqual(p_env.full_list, ('somerset', 'Peppers'))
        self.assertTrue(p_env.installed)

        peppers = self.prst.group('Peppers')
        somerset = self.prst.group('somerset')
        self.assertTrue(all((peppers.installed, somerset.installed)))
