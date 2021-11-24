#!/usr/bin/env python3
# Copyright 2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from git import Repo
import re
import sys

BOT_DISCLAIMER_MESSAGE = (
    'This is an automated message from a bot trying to be '
    "helpful.  If I'm mis-behaving, or if this message seems "
    'to be wrong, please feel free to reach out to my owner, '
    'jrosenth@chromium.org.')


REVIEW_STRICTLY_DO_NOT_SUBMIT = -1
REVIEW_PREFER_NOT_SUBMITTED = -1
REVIEW_NEEDS_HUMAN_APPROVAL = 1
REVIEW_AUTOMATIC_APPROVAL = 1


def check_upstream_commit(commit_message):
    return (
        REVIEW_STRICTLY_DO_NOT_SUBMIT,
        """The UPSTREAM tag is obsolete and should no longer be used.

If you are cherry-picking from upstream to a release branch, you should
use the BACKPORT tag, regardless if the cherry-pick is clean or not.

If you are cherry-picking from upstream to a main branch, or your PR was
merged into a release branch upstream, then Copybara should copy your CL
to the appropriate branch within 24 hours.

Note, if you would like an automated approval on backports to a
release branch, simply wait for Copybara to copy your CL to the main
branch, and then use the "Cherry-Pick" button in the Gerrit UI to copy
the CL to a release branch, adding the BACKPORT tag.  You can then add
the Rubber Stamper bot as a reviewer on the CL and it will
auto-approve.""",
    )


def check_backport_commit(commit_message):
    return (
        REVIEW_NEEDS_HUMAN_APPROVAL,
        "Reviewers: please identify if this BACKPORT commit is acceptable to "
        "merge into the release branch.",
    )


def check_frompull_commit(commit_message):
    p = re.compile(re.escape("https://github.com/zephyrproject-") + r".*/pull/[0-9]+")
    m = p.search(commit_message)
    if not m:
        return (
            REVIEW_STRICTLY_DO_NOT_SUBMIT,
            "Please add a link to the pull request in the commit message.",
        )
    return (
        REVIEW_NEEDS_HUMAN_APPROVAL,
        "Reviewers: please identify if this FROMPULL commit is acceptable "
        "to merge to our Chromium OS branches.",
    )


def check_chromium_commit(commit_message):
    return (
        REVIEW_PREFER_NOT_SUBMITTED,
        "The CHROMIUM tag is used for commits in this repository which "
        "cannot be upstreamed.\n"
        "\n"
        "Generally speaking, almost all commits can either be "
        "upstreamed, or instead landed in one of our local "
        "repositories, such as platform/ec.\n"
        "\n"
        "* If it's possible to upstream this CL, please do so.  You "
        "can reupload this CL with the FROMPULL tag instead after "
        "uploading the pull request.\n"
        "\n"
        "* Otherwise, if it's possible to land this code in "
        "platform/ec or another local repository instead, please do "
        "that, and abandon this CL.\n"
        "\n"
        "If none of the above are possible, you may remove my CR-1 on "
        "this CL and proceed with the review.\n"
        "\n"
        "Thanks for helping us keep upstream first!\n",
    )


zephyr_tags = [
    (
        "BACKPORT",
        check_backport_commit,
        "This tag should be used for commits which have already merged into "
        "upstream Zephyr main branch, and you are cherry-picking to a "
        "release branch.  Note that this tag is now used regardless if the "
        "cherry-pick was clean or not.",
    ),
    (
        "FROMPULL",
        check_frompull_commit,
        "This tag should be used for commits which have not yet been merged "
        "into upstream Zepyhr, but have a pending pull request open.  Please "
        "link to the pull request in the commit message.",
    ),
    (
        "CHROMIUM",
        check_chromium_commit,
        "This tag should be used for commits which will never be upstreamed. "
        "Generally speaking, these commits can almost always be avoided by "
        "landing code in one of the repositories we maintain (i.e., platform/ec), "
        "and should only be used as a last resort if it's impossible to put it in "
        "one of our modules, and upstream won't accept our change.  Please "
        "include adequate justification as to why this commit cannot be "
        "upstreamed in your commit message.",
    ),
    ("UPSTREAM", check_upstream_commit, "This tag should never be used."),
]


def zephyr_get_review(commit_message):
    for tag, review_func, helpmsg in zephyr_tags:
        if commit_message.startswith("{}: ".format(tag)):
            return review_func(commit_message)

    # No tag matched
    msg = """Your commit message subject line in this repository MUST include one
of the following tags to help us track upstream changes:

"""
    for tag, review_func, helpmsg in zephyr_tags:
        if tag == "UPSTREAM":
            continue
        msg += "* {}: {}\n\n".format(tag, helpmsg)

    return REVIEW_STRICTLY_DO_NOT_SUBMIT, msg


def main():
    repo = Repo(".")
    c = repo.commit("HEAD")
    ret, msg = zephyr_get_review(c.message)
    print(msg)
    print("\n")
    print(BOT_DISCLAIMER_MESSAGE)
    return ret < 0


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)
