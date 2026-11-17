{
  description = "Optional Linux development shell for the anonymous frozen-feature study";

  # All reviewer environments use Python 3.11. Scientific Python packages come
  # from the portable reviewer requirements, separately for each model stack.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/50ab793786d9de88ee30ec4e4c24fb4236fc2674";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          bashInteractive coreutils git curl cacert pkg-config
          python311
        ];
        CBMP_NIX_SHELL = "1";
        PYTHONNOUSERSITE = "1";
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
          pkgs.stdenv.cc.cc.lib pkgs.zlib pkgs.glib pkgs.libGL
        ];
        shellHook = ''
          unset PYTHONPATH
          if [ -t 1 ]; then
            printf '%s\n' 'Optional Nix shell: bash scripts/nix_setup.sh heads'
            printf '%s\n' 'Then: source scripts/nix_env.sh (see docs/NIX.md)'
          fi
        '';
      };
    };
}
