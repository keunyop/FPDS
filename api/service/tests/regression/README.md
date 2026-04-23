# FPDS API Regression Tests

Use this folder for bug-fix regression coverage that should stay runnable as a separate recursive suite.

Current structure:
- `auth/`: login/auth migration regressions

Recommended commands from `api/service`:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"
```

For a deeper recursive run inside one area:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests/regression/auth -p "test_*.py"
```
