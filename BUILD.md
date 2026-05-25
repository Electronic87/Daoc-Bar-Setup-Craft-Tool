# Build Notes

This app is a Windows Tkinter/PyInstaller desktop tool.

## Build The Exe

1. Install Python 3.12 or newer for Windows.
2. From this repo folder, install the build dependency:

   ```powershell
   py -m pip install -r requirements-dev.txt
   ```

3. Build the app:

   ```powershell
   py -m PyInstaller --noconfirm --clean "Daoc Craft tool V3.spec"
   ```

4. The executable will be created at:

   ```text
   dist\Daoc Bar setup and craft tool v3.0.2.exe
   ```

## Release Packaging

For GitHub, prefer publishing the compiled `.exe` and `.zip` under GitHub Releases instead of committing binaries into the repo.

A simple release zip should contain:

- `Daoc Bar setup and craft tool v3.0.2.exe`
- `README.txt`

## Notes

- The app writes user settings to `%APPDATA%\Daoc Craft tool\settings.json` when running as a frozen exe.
- The app intentionally displays Windows user-profile paths as `C:\Users\%username%\...`.
- The PyInstaller spec includes Tcl/Tk data from the Python runtime used to build the app.
