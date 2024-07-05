{
  description = "Development flake environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/23.11";

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem
    (system: let
      pkgs = import nixpkgs {
        inherit system;
      };
    in {
      devShells.default = pkgs.mkShell {
        buildInputs = [
          pkgs.pre-commit
        ];

        shellHook = ''
          VENV=.venv
          if test -d $VENV; then
            source ./$VENV/bin/activate
          fi
        '';
      };
    });
}
