{inputs, ...}: {
  imports = [
    # Reads ./devenv.config.toml and populates config.devLayers.<role>.*,
    # conditionally importing provider layers per the role selection there.
    (import (inputs.devenv-layers + "/dev-layers/devenv.nix") {
      configPath = ./devenv.config.toml;
    })

    (inputs.devenv-layers + "/common/devenv.nix")
    (inputs.devenv-layers + "/languages/python/3.12.x/devenv.nix")
  ];

  # Dependencies are declared in pyproject.toml and pinned in uv.lock; devenv runs
  # `uv sync` on shell entry so the venv under $DEVENV_STATE/venv always matches.
  languages.python.uv = {
    enable = true;
    sync = {
      enable = true;
      allGroups = true;
    };
  };

  # The layer's pylint hook runs a Nix pylint outside the project venv, so it cannot
  # resolve third-party imports. Point it at the venv's pylint.
  git-hooks.hooks.pylint.settings.binPath = "pylint";
  git-hooks.hooks.ruff.enable = true;

  enterShell = ''
    export PYTHONPATH=$PYTHONPATH:$(pwd)
  '';
}
