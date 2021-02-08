:orphan:

.. _contribute:

**************************************************
How to contribute to the sources of the project
**************************************************

Install a dev version
##########################

The best way to contribute to the development of the source code is to:

1. Fork the official Macatools repo of macapype on your github account

2. Clone your forked repo in local and make it the installed package

.. code-block:: bash

    git clone https://github.com/my_github_account/macapype.git
    cd macapype
    python setup develop

(or, if you do not have root access:)

.. code-block:: bash

    python setup develop --user

3. Add the official Macatools repository (or remote) under the name "upstream":

.. code-block:: bash

    git remote add upstream https://github.com/Macatools/macapype.git

4. Make a new branch, corresponding to your modified feature:

.. code-block:: bash

    git checkout -b my_new_feature

5. Do the modifications, test them on provided examples. All the intermediate modifications are commited/pushed to your branch, in your remote:

.. code-block:: bash

    git commit -a -m"My modifications"
    git push origin my_new_feature

6. Once your are satisfied with modifications in your local remote on my_new_feature branch, create a pull request (PR) to merge your branch with the official Macatools repo (see below)

Pull Request
#############

Some indications on how to create a PR:

1. The title of the PR should be as informative as possible about the modifications that have been done to the project (as it will be used in the forthcoming changelog). Adding some prefixes can also be useful (from the nipype documentation, but seems standard):

* [ENH] for enhancements

* [FIX] for bug fixes

* [TST] for new or updated tests

* [DOC] for new or updated documentation

* [STY] for stylistic changes

* [REF] for refactoring existing code

2. It is also good practice to reduce as few as possible the number of commit messages. One standard way to do it is to use the rebase command, that allows to have a linear commit history. However, rebase can be tricky sometimes, in particular if several contributors have worked on a pull request. It is sometimes necessary (and nothing to be ashamed of!) to make a temporary copy, stat from a fresh version, and commit all your changes at once after creating a new branch. Here the typical way of rebasing your code:


.. code-block:: bash

    git fetch uptream
    git rebase -i upstream/master

Here, all your commits will appear in a list. Normally you should keep (i.e. "pick" or "p") the oldest one (i.e. the one at the top of the list) and "fixup" (or "f") all remaining commits. If you are not satisfied of the commit message of the first commit, you can use "reword" (or "r") to reword the commit message that will be kept. You then will be asked to force-push your rebased version

.. code-block:: bash

    git push -f origin my_new_feature


3. Once you are happy with all the previous steps, you can add a [MRG] for specifying that your branch is now ready to be merged, and create the PR (normally github automatically propose to create a PR when a new branch have been detected). Typically the PR should be from my_github_account:my_new_feature to macatools:master

4. A PR requires both automated checking and  "manual" reviewing. The automated checking corresponds to the automated checks, mostly unit tests and coverage. The manual reviewing is not mandatory, but highly recommended, as it is good practice that the merging is done by someone different than the person requesting the PR.

5. Once the PR is merged, you may delete the branch directly on your remote (i.e. your github account) as proposed by github. It is also good practice to delete the branch of local copy, and get the latest version in your master branch. Hence your local copy is similar to what you would have if you just cloned the newest master version of upstream.

.. code-block:: bash

    git checkout master
    git pull upstream master
    git branch -D my_new_feature





