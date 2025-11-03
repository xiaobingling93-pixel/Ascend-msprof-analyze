# Copyright (C) 2025. Huawei Technologies Co., Ltd. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest.mock import patch

from msprof_analyze.advisor.common.timeline.fusion_ops_rule_handler import TimelineOpRuleHandler


class TestTimelineOpRuleHandler(unittest.TestCase):
    """UT for TimelineOpRuleHandler"""

    def test_set_db_content_when_with_invalid_items_then_filters_and_generates(self):
        handler = TimelineOpRuleHandler()
        db_content = [
            None,
            {},
            {"no_unique_id": 1},
            {"unique_id": 1, "operator_rules": {"aten": {"add": {"k1": ["v1"]}}}},
            {"unique_id": 2, "inherit_unique_id": 1, "operator_rules": {"aten": {"add": {"k2": ["v2"]}}}},
        ]

        handler.set_db_content(db_content)

        self.assertIn(1, handler._all_origin_timeline_op_rule_dict)
        self.assertIn(2, handler._all_origin_timeline_op_rule_dict)
        self.assertIn(1, handler._all_tmp_timeline_op_rule)
        self.assertIn(2, handler._all_tmp_timeline_op_rule)

    def test_generate_basic_timeline_op_rules_when_called_then_only_basic_added(self):
        handler = TimelineOpRuleHandler()
        handler._all_origin_timeline_op_rule_dict = {
            1: {"unique_id": 1, "operator_rules": {"aten": {"add": {"k1": ["v1"]}}}},
            2: {"unique_id": 2, "inherit_unique_id": 1, "operator_rules": {"aten": {"add": {"k2": ["v2"]}}}},
        }

        handler.generate_basic_timeline_op_rules()

        self.assertIn(1, handler._exist_timeline_op_rule_unique_id_list)
        self.assertIn(1, handler._all_tmp_timeline_op_rule)
        self.assertNotIn(2, handler._all_tmp_timeline_op_rule)

    def test_add_basic_timeline_op_rule_when_with_local_inherit_then_skip(self):
        handler = TimelineOpRuleHandler()
        rule_dic = {
            "unique_id": 3,
            "operator_rules": {
                "aten": {
                    "inherit_unique_id": 1
                }
            }
        }

        handler.add_basic_timeline_op_rule(rule_dic)

        self.assertNotIn(3, handler._all_tmp_timeline_op_rule)
        self.assertNotIn(3, handler._exist_timeline_op_rule_unique_id_list)

    def test_add_empty_timeline_op_rule_when_called_then_creates_empty_rule(self):
        handler = TimelineOpRuleHandler()

        handler.add_empty_timeline_op_rule(4)

        self.assertIn(4, handler._all_tmp_timeline_op_rule)
        self.assertEqual(handler._all_tmp_timeline_op_rule[4], {})
        self.assertIn(4, handler._exist_timeline_op_rule_unique_id_list)

    def test_generate_specified_timeline_op_rule_when_missing_then_empty_created(self):
        handler = TimelineOpRuleHandler()

        handler.generate_specified_timeline_op_rule(5)

        self.assertIn(5, handler._all_tmp_timeline_op_rule)
        self.assertEqual(handler._all_tmp_timeline_op_rule[5], {})

    def test_generate_specified_timeline_op_rule_when_with_cycle_then_no_inherit(self):
        handler = TimelineOpRuleHandler()
        handler._all_origin_timeline_op_rule_dict = {
            6: {"unique_id": 6, "inherit_unique_id": 7, "operator_rules": {"aten": {"add": {"k6": ["v6"]}}}},
            7: {"unique_id": 7, "inherit_unique_id": 6, "operator_rules": {"aten": {"add": {"k7": ["v7"]}}}},
        }

        handler.generate_specified_timeline_op_rule(6)
        handler.generate_specified_timeline_op_rule(7)

        self.assertIn(6, handler._all_tmp_timeline_op_rule)
        self.assertEqual(handler._all_tmp_timeline_op_rule[6], {'aten': {'k6': ['v6'], 'k7': ['v7']}})

    def test_generate_specified_timeline_op_rule_when_with_global_and_local_inherit_then_merged(self):
        handler = TimelineOpRuleHandler()
        # base rule 10
        handler._all_origin_timeline_op_rule_dict = {
            10: {"unique_id": 10, "operator_rules": {"aten": {"add": {"base": ["B"]}}}},
            11: {
                "unique_id": 11,
                "inherit_unique_id": 10,
                "operator_rules": {
                    "aten": {
                        # local inherit from 10 as well (redundant but exercises path)
                        "inherit_unique_id": 10,
                        "add": {"child": ["C"]}
                    }
                }
            },
        }

        handler.generate_specified_timeline_op_rule(11)

        self.assertIn(11, handler._all_tmp_timeline_op_rule)
        merged = handler._all_tmp_timeline_op_rule[11]
        # should contain keys from base and child under 'aten'
        self.assertIn("aten", merged)
        self.assertIn("base", merged["aten"])  # from base
        self.assertIn("child", merged["aten"])  # from child

    def test_generate_all_timeline_op_rule_when_called_then_all_generated(self):
        handler = TimelineOpRuleHandler()
        handler._all_origin_timeline_op_rule_dict = {
            20: {"unique_id": 20, "operator_rules": {"aten": {"add": {"k20": ["v20"]}}}},
            21: {"unique_id": 21, "inherit_unique_id": 20, "operator_rules": {"aten": {"add": {"k21": ["v21"]}}}},
        }

        handler.generate_all_timeline_op_rule()

        self.assertIn(20, handler._all_tmp_timeline_op_rule)
        self.assertIn(21, handler._all_tmp_timeline_op_rule)

    def test_get_tmp_timeline_op_rule_with_unique_id_when_unknown_then_empty_added(self):
        handler = TimelineOpRuleHandler()

        result = handler.get_tmp_timeline_op_rule_with_unique_id(30)

        self.assertEqual(result, {})
        self.assertIn(30, handler._all_tmp_timeline_op_rule)

    @patch('msprof_analyze.advisor.common.timeline.fusion_ops_rule_handler.logger')
    def test_get_tmp_timeline_op_rule_with_unique_id_when_negative_then_logs_error_and_returns_empty(self, mock_logger):
        handler = TimelineOpRuleHandler()

        result = handler.get_tmp_timeline_op_rule_with_unique_id(-1)

        self.assertEqual(result, {})
        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()


