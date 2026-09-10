{
  description = "Kinect Canvas Loop installation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];

      forEachSystem = f:
        nixpkgs.lib.genAttrs systems (system:
          f {
            pkgs = import nixpkgs {
              inherit system;
            };
          });

      runtimeLibraries = pkgs: with pkgs; [
        libxcb
        libX11
        libXcursor
        libXi
        libXrandr
        libXext
        libXinerama
        libXrender
        libXScrnSaver
        mesa
        libGL
        glib
      ];
    in {
      devShells = forEachSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            # Python
            python312
            uv

            # C/C++
            gcc
            cmake
            gnumake
            pkg-config

            # Kinect
            freenect
            libusb1

            # C++ dependencies
            opencv
            qt6.qtbase
            qt6.qttools
            freeglut
            libGLU
            zeromq
            libsodium
            cppzmq
            gtest

            # Python/Pygame dependencies
            SDL2
            SDL2_image
            SDL2_mixer
            SDL2_ttf
          ] ++ runtimeLibraries pkgs;

          shellHook = ''
            export LD_LIBRARY_PATH="${
              pkgs.lib.makeLibraryPath (runtimeLibraries pkgs)
            }:$LD_LIBRARY_PATH"

            export PKG_CONFIG_PATH="${
              pkgs.lib.makeSearchPath "lib/pkgconfig" [
                pkgs.freenect
                pkgs.zeromq
              ]
            }:$PKG_CONFIG_PATH"

            export SDL_VIDEODRIVER=''${SDL_VIDEODRIVER:-x11}

            echo "Kinect Canvas Loop development shell"
            echo "DISPLAY: ''${DISPLAY:-not set}"
          '';
        };
      });
    };
}
