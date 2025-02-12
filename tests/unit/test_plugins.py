# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import babel
from mock import Mock

import searx.plugins
import searx.preferences
import searx.results

from searx.result_types import Result
from searx.extended_types import sxng_request

from tests import SearxTestCase

plg_store = searx.plugins.PluginStorage()
plg_store.load_builtins()


def get_search_mock(query, **kwargs):

    lang = kwargs.get("lang", "en-US")
    kwargs["pageno"] = kwargs.get("pageno", 1)
    kwargs["locale"] = babel.Locale.parse(lang, sep="-")
    user_plugins = kwargs.pop("user_plugins", [x.id for x in plg_store])

    return Mock(
        search_query=Mock(query=query, **kwargs),
        user_plugins=user_plugins,
        result_container=searx.results.ResultContainer(),
    )


def do_pre_search(query, storage, **kwargs) -> bool:

    search = get_search_mock(query, **kwargs)
    ret = storage.pre_search(sxng_request, search)
    return ret


def do_post_search(query, storage, **kwargs) -> Mock:

    search = get_search_mock(query, **kwargs)
    storage.post_search(sxng_request, search)
    return search


class PluginMock(searx.plugins.Plugin):

    def __init__(self, _id: str, name: str, default_enabled: bool = False):
        self.id = _id
        self._name = name
        self.default_enabled = default_enabled
        self.info = searx.plugins.PluginInfo(
            id=id,
            name=name,
            description=f"Dummy plugin: {id}",
            preference_section="general",
        )
        super().__init__()

    # pylint: disable= unused-argument
    def pre_search(self, request, search) -> bool:
        return True

    def post_search(self, request, search) -> None:
        return None

    def on_result(self, request, search, result) -> bool:
        return False


class PluginStorage(SearxTestCase):

    def setUp(self):
        super().setUp()
        engines = {}

        searx.settings['enabled_plugins'] = [
            {
                'name': 'plg001',
            },
            {
                'name': 'plg002',
            },
        ]
        self.storage = searx.plugins.PluginStorage()
        self.storage.register(PluginMock("plg001", "first plugin"))
        self.storage.register(PluginMock("plg002", "second plugin"))
        self.storage.init(self.app)
        self.pref = searx.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def test_init(self):

        self.assertEqual(2, len(self.storage))

    def test_hooks(self):

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            query = ""

            ret = do_pre_search(query, self.storage, pageno=1)
            self.assertTrue(ret is True)

            ret = self.storage.on_result(
                sxng_request,
                get_search_mock("lorem ipsum", user_plugins=["plg001", "plg002"]),
                Result(),
            )
            self.assertFalse(ret)
