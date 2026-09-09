{
  description = "Tifo partitions - image processing project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [
            pkgs.cmake
            pkgs.gnumake
            pkgs.gcc
            pkgs.pkg-config
          ];

          buildInputs = [
            pkgs.gtest
            pkgs.opencv
            pkgs.freetype
            pkgs.qt6.qtbase
            pkgs.qt6.qttools
            pkgs.freenect
            pkgs.freeglut
            pkgs.libGLU
            pkgs.zeromq
            pkgs.libsodium
            pkgs.cppzmq
          ];
        };
      });
}
