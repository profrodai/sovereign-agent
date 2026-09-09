# Set up before the session

Use Python 3.14 and a Jupyter kernel that selects that interpreter. The notebooks use Python 3.14 syntax; an older kernel can fail before the lesson begins. Basic functions, loops, lists and dictionaries are prerequisites. Pydantic, SQLite and specialized concepts are introduced inside each unit before use.

If you already have Jupyter, select a Python 3.14 kernel. Install the exact Pydantic version in that kernel once:

```python
%pip install "pydantic==2.13.4"
```

Restart the kernel after installation. Package installation requires internet; the core lessons run offline without model credentials, a Telegram account or a supplier account. A notebook includes its own frozen teaching runtime and writes scratch files into a temporary directory. Keep your edited notebook and saved handoff/evidence files outside scratch cleanup.

## Prepare this download on a new machine

A **virtual environment** keeps the course's Python packages separate from other projects. **JupyterLab** is the browser interface in which you open a notebook; **ipykernel** is the Python process that runs its cells. **uv** creates the environment and installs its packages. These tools are environment preparation, not concepts you need to derive to complete the agent exercises.

Install uv using its [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/), then open a new terminal and check `uv --version`. Extract this asset's ZIP into a writable folder. Open a terminal **in that extracted folder**, beside this SETUP.md. No repository clone or other teaching asset is needed.

On macOS or Linux:

```bash
uv venv --python 3.14 --seed .venv
uv pip install --python .venv/bin/python "jupyterlab==4.6.3" "ipykernel==7.3.0" "pydantic==2.13.4"
.venv/bin/python -m jupyterlab
```

On Windows PowerShell:

```powershell
uv venv --python 3.14 --seed .venv
uv pip install --python .venv/Scripts/python.exe "jupyterlab==4.6.3" "ipykernel==7.3.0" "pydantic==2.13.4"
.venv/Scripts/python.exe -m jupyterlab
```

The first command obtains Python 3.14 if necessary and creates `.venv`; `--seed` supplies pip for notebook `%pip` commands. The second installs the notebook interface, kernel and lesson dependency. The third starts JupyterLab using this environment's Python. Keep the terminal open while working. JupyterLab opens a local browser page; if it does not, use the local URL printed by the command. Do not share that session URL.

In JupyterLab's file browser open the selected chapter folder and `unit-a.ipynb` (educators choose its local `student` or `solutions` folder). Select its Python 3 kernel, then run this cell to verify which interpreter is actually running:

```python
import sys
import pydantic

print(sys.executable)
print(sys.version)
print(pydantic.__version__)
assert sys.version_info[:2] == (3, 14)
assert pydantic.__version__ == "2.13.4"
```

Expect the executable inside your extracted asset's `.venv`, Python 3.14.x and Pydantic 2.13.4. If the assertions fail, select the local environment kernel before beginning; reinstalling packages into an unrelated terminal interpreter will not fix a wrong kernel. Save with Ctrl+S or Command+S. Stop the server with Ctrl+C in its terminal when finished.

These commands follow the official [environment](https://docs.astral.sh/uv/pip/environments/), [JupyterLab installation](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html) and [startup](https://jupyterlab.readthedocs.io/en/stable/getting_started/starting.html) documentation. The package set resolved for Python 3.14 during preparation. This migration's notebook checks execute kernels; a graphical JupyterLab session and Windows setup have not been observed in this change.

Environment setup is separate from the ninety-minute work plan. A notebook that reports NEEDS_WORK is running as intended: you must complete the exercise functions before it can report successful work.

Open Unit A to construct the mechanism. Unit B includes a labelled reference start or accepts your explicitly selected successful Unit A handoff through LEARNER_HANDOFF. Reference starts do not earn credit for your prior construction. Run each cell in order, make a prediction before observing output, and retain a first attempt before consulting a worked solution.

[Asset index](README.md)
