#!/usr/bin/env python3
"""Update GitHub tool statuses in metatools namespace."""

import os
from buildmcp.metamcp import MetaMCPClient


# Active tools (read-only/query operations)
ACTIVE_TOOLS = [
    # Code & File Access
    "search_code",
    "get_file_contents",
    # Repository Information
    "search_repositories",
    "list_branches",
    "list_tags",
    "get_tag",
    "list_commits",
    "get_commit",
    "list_releases",
    "get_latest_release",
    "get_release_by_tag",
    # Issues & PRs (Read)
    "search_issues",
    "list_issues",
    "get_issue",
    "get_issue_comments",
    "list_sub_issues",
    "search_pull_requests",
    "list_pull_requests",
    "get_pull_request",
    "get_pull_request_diff",
    "get_pull_request_files",
    "get_pull_request_reviews",
    "get_pull_request_review_comments",
    "get_pull_request_status",
    # Discussions
    "list_discussions",
    "get_discussion",
    "get_discussion_comments",
    "list_discussion_categories",
    # Workflow & CI/CD (Read)
    "list_workflows",
    "list_workflow_runs",
    "get_workflow_run",
    "list_workflow_jobs",
    "get_job_logs",
    "get_workflow_run_logs",
    "get_workflow_run_usage",
    "list_workflow_run_artifacts",
    "download_workflow_run_artifact",
    # Security & Alerts (Read)
    "list_code_scanning_alerts",
    "get_code_scanning_alert",
    "list_dependabot_alerts",
    "get_dependabot_alert",
    "list_secret_scanning_alerts",
    "get_secret_scanning_alert",
    "list_global_security_advisories",
    "get_global_security_advisory",
    "list_repository_security_advisories",
    "list_org_repository_security_advisories",
    # User & Organization
    "get_me",
    "search_users",
    "search_orgs",
    "get_teams",
    "get_team_members",
    # Projects & Gists
    "list_projects",
    "get_project",
    "list_project_items",
    "get_project_item",
    "list_project_fields",
    "get_project_field",
    "list_gists",
    # Notifications (Read)
    "list_notifications",
    "get_notification_details",
    # Copilot
    "list_copilot_spaces",
    "get_copilot_space",
    # Miscellaneous
    "list_starred_repositories",
    "list_issue_types",
    "bing_search",
]

# Inactive tools (write/modify operations)
INACTIVE_TOOLS = [
    # File Operations
    "create_or_update_file",
    "delete_file",
    "push_files",
    # Repository Management
    "create_repository",
    "fork_repository",
    "create_branch",
    # Issues (Write)
    "create_issue",
    "update_issue",
    "add_issue_comment",
    "add_sub_issue",
    "remove_sub_issue",
    "reprioritize_sub_issue",
    # Pull Requests (Write)
    "create_pull_request",
    "create_pull_request_with_copilot",
    "update_pull_request",
    "update_pull_request_branch",
    "merge_pull_request",
    "create_pending_pull_request_review",
    "create_and_submit_pull_request_review",
    "submit_pending_pull_request_review",
    "delete_pending_pull_request_review",
    "assign_copilot_to_issue",
    "request_copilot_review",
    # Workflows (Write)
    "run_workflow",
    "rerun_workflow_run",
    "rerun_failed_jobs",
    "cancel_workflow_run",
    "delete_workflow_run_logs",
    # Gists (Write)
    "create_gist",
    "update_gist",
    # Projects (Write)
    "add_project_item",
    "delete_project_item",
    # Notifications (Write)
    "dismiss_notification",
    "mark_all_notifications_read",
    "manage_notification_subscription",
    "manage_repository_notification_subscription",
    # Social (Write)
    "star_repository",
    "unstar_repository",
]


def main():
    """Update tool statuses for metatools namespace."""
    # Get session token from environment
    session_token = os.getenv("METAMCP_SESSION_TOKEN")
    if not session_token:
        print("Error: METAMCP_SESSION_TOKEN environment variable not set")
        print("Export your session token first:")
        print('  export METAMCP_SESSION_TOKEN="your-token"')
        return 1

    # Create client
    client = MetaMCPClient(session_token=session_token)

    namespace = "metatools"
    server = "github"

    # Update active tools
    print(f"Setting {len(ACTIVE_TOOLS)} tools to ACTIVE...")
    for i, tool in enumerate(ACTIVE_TOOLS, 1):
        try:
            client.update_tool_status(
                namespace=namespace,
                server=server,
                tool=tool,
                active=True
            )
            print(f"  [{i}/{len(ACTIVE_TOOLS)}] ✓ {tool}")
        except Exception as e:
            print(f"  [{i}/{len(ACTIVE_TOOLS)}] ✗ {tool}: {e}")

    # Update inactive tools
    print(f"\nSetting {len(INACTIVE_TOOLS)} tools to INACTIVE...")
    for i, tool in enumerate(INACTIVE_TOOLS, 1):
        try:
            client.update_tool_status(
                namespace=namespace,
                server=server,
                tool=tool,
                active=False
            )
            print(f"  [{i}/{len(INACTIVE_TOOLS)}] ✓ {tool}")
        except Exception as e:
            print(f"  [{i}/{len(INACTIVE_TOOLS)}] ✗ {tool}: {e}")

    print(f"\n✓ Updated {len(ACTIVE_TOOLS)} active and {len(INACTIVE_TOOLS)} inactive tools")
    return 0


if __name__ == "__main__":
    exit(main())
