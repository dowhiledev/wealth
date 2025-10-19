Contributing to WealthOS
========================

Thanks for your interest in contributing! This guide keeps things simple so you can be productive quickly.

Ways to contribute
------------------

- Bug reports — Open issues with clear steps to reproduce.
- Feature requests — Describe the problem, not only the solution. Screenshots/mockups help.
- Code contributions — Fix bugs, add features, improve docs and tests.

Dev setup
---------

1) Prereqs: Python 3.11+, Node.js 18+, uv (or your preferred virtual env tool)
2) Install Python deps: `uv sync`
3) (Optional) Configure `.env` (copy from `.env.example`)
4) Initialize DB: `uv run wealth init` (or `uv run python -m wealth_os init`)
5) Run API + UI
   - Prod UI: `uv run wealth ui --build`
   - Dev UI: `uv run wealth ui --dev`

Code style & tests
------------------

- Keep changes focused; avoid unrelated refactors.
- Follow existing naming and file structure.
- Run tests: `uv run pytest -q`
- UI changes should build locally: `cd src/wealth_os/ui && npm install && npm run build`

Pull requests
-------------

- Fork the repo, create a branch, make your changes.
- Include a concise description of the change and screenshots for UI changes.
- Link any related issues.

License
-------

By contributing, you agree that your contributions will be licensed under the MIT license (see LICENSE).

Releases
--------

Maintainers: see the “Publish to PyPI” section in README.md for building and uploading distributions.
