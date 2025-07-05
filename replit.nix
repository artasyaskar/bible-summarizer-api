
{ pkgs }: {
  # Specify the Nix packages to make available in the environment
  deps = [
    # Use a specific Python version, e.g., Python 3.11
    # pkgs.python311Full provides python3.11, pip, and other common tools.
    pkgs.python311Full 
    
    # Replit's debugger integration tool, version should match Python.
    pkgs.replitPackages.prybar-python311 

    # Add other system-level dependencies if your project needs them.
    # For example, if a Python package has non-Python dependencies:
    # pkgs.git 
    # pkgs.openssl
    # pkgs.zlib
    # For PyTorch/Transformers, usually the prebuilt wheels work without extra system libs here,
    # but if you encounter issues with shared libraries (.so files), they might be added here.
  ];

  # Environment variables to set within the Nix shell
  env = {
    # Standard environment path for Python shared libraries.
    # This helps Python find system libraries if any are installed via Nix.
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      # Add packages here if their .so files need to be in the library path
      # e.g., pkgs.openssl.lib, pkgs.zlib.out 
    ];
    
    # Standard path for Python executables
    PYTHONBIN = "${pkgs.python311Full}/bin/python3.11";
    
    # Standard locale settings
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8"; # Explicitly set LC_ALL as well for good measure
    
    # Replit specific environment variables for their tooling
    STDERREDIT_BINARY = "${pkgs.replitPackages.stderredit}/bin/stderredit";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python311}/bin/prybar-python311";

    # Ensure pip user packages are in PATH (Replit usually handles this)
    # PATH = "${pkgs.python311Full}/bin:${env.PATH}"; # Example, usually not needed to override PATH directly like this
  };
}
