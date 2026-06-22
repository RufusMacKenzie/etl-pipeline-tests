import sys
import json
import os
import subprocess
import anthropic


def get_git_diff():
    # run git diff HEAD~1 and return output
    command = ["git", "diff", "HEAD~1"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Git Error Output:\n{e.stderr}"


def parse_test_results(report_path):
    with open(report_path, "r") as f:
        report = json.load(f)

    """
    report will have content like this:
    {
        "summary": {"passed": 30, "failed": 1, "total": 31, "duration": 0.13},
        "tests": [
            {
                "nodeid": "tests/test_extract.py::test_returns_correct_record_count",
                "outcome": "passed",
                "duration": 0.001
            },
            {
                "nodeid": "tests/test_transform.py::test_something",
                "outcome": "failed",
                "call": {
                    "longrepr": "full traceback here..."
                }
            }
        ]
    }
    """

    summary = report["summary"]
    tests = report["tests"]

    passed = [t["nodeid"] for t in tests if t["outcome"] == "passed"]
    failed = [
        {
            "test": t["nodeid"],
            "error": t.get("call", {}).get("longrepr", "No details available"),
        }
        for t in tests
        if t["outcome"] == "failed"
    ]

    return {"summary": summary, "passed": passed, "failed": failed}


def build_prompt(diff, test_results):
    summary = test_results["summary"]
    passed = "\n".join(test_results["passed"])
    failed = (
        "\n".join(
            f"TEST: {f['test']}\nERROR: {f['error']}" for f in test_results["failed"]
        )
        or "None"
    )

    return f"""
You are a QA engineer analyzing test results and code changes.

## Git Diff
{diff}

## Test Summary
Total: {summary["total"]} | Passed: {summary.get("passed", 0)} | Failed: {summary.get("failed", 0)}

## Passed Tests
{passed}

## Failed Tests
{failed}

## Analysis Request
1. What code changed?
2. Which existing tests cover those changes?
3. What test gaps exist?
"""


def post_github_comment(analysis):
    # use gh CLI or requests to post commit comment
    repo = os.environ.get("GITHUB_REPOSITORY")
    sha = os.environ.get("GITHUB_SHA")

    comment = f"## 🤖 AI Test Analysis\n\n{analysis}"

    subprocess.run(
        ["gh", "api", f"/repos/{repo}/commits/{sha}/comments", "-f", f"body={comment}"],
        check=True,
    )


def main():
    try:
        diff = get_git_diff()
        test_summary = parse_test_results("test-report.json")
        prompt = build_prompt(diff, test_summary)

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        analysis = message.content[0].text
        post_github_comment(analysis)
        print("✅ Analysis complete and posted")

    except Exception as e:
        print(f"⚠️ Analysis step failed: {e}")
        # Exit with 0 so workflow doesn't fail
        # The error is visible in the Actions log
        sys.exit(0)


if __name__ == "__main__":
    main()
