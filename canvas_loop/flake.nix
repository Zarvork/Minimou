{
  description = "Pygame/OpenCV development shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
      };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python312
          uv
          pkg-config

          # Pygame / SDL
          SDL2
          SDL2_image
          SDL2_mixer
          SDL2_ttf

          # OpenCV / affichage X11
          libxcb
          libX11
          libXcursor
          libXi
          libXrandr
          libXext
          libXinerama
          libXrender
          libXScrnSaver

          # Certaines installations OpenCV en ont besoin
          mesa
          libGL
          glib
        ];

        shellHook = ''
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
            pkgs.libxcb
            pkgs.libX11
            pkgs.libXcursor
            pkgs.libXi
            pkgs.libXrandr
            pkgs.libXext
            pkgs.libXinerama
            pkgs.libXrender
            pkgs.libXScrnSaver
            pkgs.mesa
            pkgs.libGL
            pkgs.glib
          ]}:$LD_LIBRARY_PATH"

          export SDL_VIDEODRIVER=''${SDL_VIDEODRIVER:-x11}

          echo "Pygame/OpenCV development shell"
          echo "DISPLAY: ''${DISPLAY:-not set}"
        '';
      };
    };
}