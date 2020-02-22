import os
from textwrap import dedent

from jupyter_cache.git_cache import JupyterCacheGit


NB_PATH = os.path.join(os.path.realpath(os.path.dirname(__file__)), "notebooks")


def test_basic_workflow(tmp_path, data_regression):
    db = JupyterCacheGit(str(tmp_path))
    db.stage_notebook_file(path=os.path.join(NB_PATH, "basic.ipynb"), uri="basic.ipynb")
    db.stage_notebook_file(
        path=os.path.join(NB_PATH, "basic.ipynb"), uri="basic2.ipynb"
    )
    assert db.list_staged_notebooks() == {"basic.ipynb", "basic2.ipynb"}
    assert db.list_committed_notebooks() == set()
    db.commit_all()
    assert db.list_staged_notebooks() == set()
    assert db.list_committed_notebooks() == {"basic.ipynb", "basic2.ipynb"}
    db.invalidate_notebook("basic.ipynb")
    db.remove_notebook("basic2.ipynb")
    assert db.list_staged_notebooks() == {"basic.ipynb"}
    assert db.list_committed_notebooks() == set()  # TODO this should be {"basic.ipynb"}

    db.commit_all()
    assert db.list_staged_notebooks() == set()
    assert db.list_committed_notebooks() == {"basic.ipynb"}

    # commit a notebook then change its text cell
    db.stage_notebook_file(
        path=os.path.join(NB_PATH, "basic.ipynb"), uri="basic2.ipynb"
    )
    db.commit_all()
    nb_bundle = db.get_committed_notebook("basic2.ipynb")
    nb_bundle.nb.cells[0].source = "# New Title"
    db.stage_notebook_bundle(nb_bundle)
    # change the source code of a committed notebook
    nb_bundle = db.get_committed_notebook("basic.ipynb")
    nb_bundle.nb.cells[1].source = "print('hi')"
    db.stage_notebook_bundle(nb_bundle)
    # stage another notebook
    db.stage_notebook_file(
        path=os.path.join(NB_PATH, "basic.ipynb"), uri="basic3.ipynb"
    )

    assert db.list_staged_notebooks() == {"basic.ipynb", "basic3.ipynb", "basic2.ipynb"}
    assert db.list_committed_notebooks() == {"basic2.ipynb", "basic.ipynb"}
    assert db.diff_staged_notebook(
        "basic.ipynb", as_str=True, use_color=False
    ) == dedent(
        """\
        nbdiff basic.ipynb
        --- committed
        +++ staged
        ## inserted before nb/cells/1:
        +  code cell:
        +    execution_count: 2
        +    source:
        +      print('hi')
        +    outputs:
        +      output 0:
        +        output_type: stream
        +        name: stdout
        +        text:
        +          1

        ## deleted nb/cells/1:
        -  code cell:
        -    execution_count: 2
        -    source:
        -      a=1
        -      print(a)
        -    outputs:
        -      output 0:
        -        output_type: stream
        -        name: stdout
        -        text:
        -          1

        """
    )

    to_exec = [nb_bundle.uri for nb_bundle in db.iter_notebooks_to_exec()]
    assert set(to_exec) == {"basic.ipynb", "basic3.ipynb"}
