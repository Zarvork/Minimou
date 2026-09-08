{
  description = "Pygame development environment on NixOS";

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

          # SDL2 / Pygame runtime
          SDL2
          SDL2_image
          SDL2_mixer
          SDL2_ttf

          # Wayland
          wayland
          libxkbcommon

          # X11 fallback
          xorg.libX11
          xorg.libXcursor
          xorg.libXi
          xorg.libXrandr
          xorg.libXext
          xorg.libXinerama
          xorg.libXrender
          xorg.libXScrnSaver

          # OpenGL / EGL
          libGL
          libGLU
        ];

        shellHook = ''
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
            pkgs.wayland
            pkgs.libxkbcommon
            pkgs.xorg.libX11
            pkgs.xorg.libXcursor
            pkgs.xorg.libXi
            pkgs.xorg.libXrandr
            pkgs.xorg.libXext
            pkgs.xorg.libXinerama
            pkgs.xorg.libXrender
            pkgs.xorg.libXScrnSaver
            pkgs.libGL
            pkgs.libGLU
          ]}:$LD_LIBRARY_PATH"

          echo "Pygame/Nix development shell"
          echo "Wayland: $WAYLAND_DISPLAY"
          echo "X11:     $DISPLAY"
        '';
      };
    };
}