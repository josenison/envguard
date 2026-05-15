"""envguard CLI sub-command registry."""
from __future__ import annotations

from envguard.commands.group_cmd import add_group_subparser, run_group
from envguard.commands.diff_cmd import add_diff_subparser, run_diff
from envguard.commands.validate_cmd import add_validate_subparser, run_validate
from envguard.commands.audit_cmd import add_audit_subparser, run_audit
from envguard.commands.export_cmd import add_export_subparser, run_export
from envguard.commands.sort_cmd import add_sort_subparser, run_sort
from envguard.commands.rename_cmd import add_rename_subparser, run_rename
from envguard.commands.trim_cmd import add_trim_subparser, run_trim
from envguard.commands.compare_cmd import add_compare_subparser, run_compare
from envguard.commands.inject_cmd import add_inject_subparser, run_inject
from envguard.commands.deduplicate_cmd import add_deduplicate_subparser, run_deduplicate
from envguard.commands.patch_cmd import add_patch_subparser, run_patch
from envguard.commands.interpolate_cmd import add_interpolate_subparser, run_interpolate
from envguard.commands.snapshot_cmd import add_snapshot_subparser, run_snapshot
from envguard.commands.profile_cmd import add_profile_subparser, run_profile

__all__ = [
    "add_group_subparser", "run_group",
    "add_diff_subparser", "run_diff",
    "add_validate_subparser", "run_validate",
    "add_audit_subparser", "run_audit",
    "add_export_subparser", "run_export",
    "add_sort_subparser", "run_sort",
    "add_rename_subparser", "run_rename",
    "add_trim_subparser", "run_trim",
    "add_compare_subparser", "run_compare",
    "add_inject_subparser", "run_inject",
    "add_deduplicate_subparser", "run_deduplicate",
    "add_patch_subparser", "run_patch",
    "add_interpolate_subparser", "run_interpolate",
    "add_snapshot_subparser", "run_snapshot",
    "add_profile_subparser", "run_profile",
]
