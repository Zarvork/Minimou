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
          buildInputs = [
            pkgs.gtest
            pkgs.cmake
            pkgs.gnumake
            pkgs.gcc
            pkgs.pkg-config
            pkgs.opencv
            pkgs.freetype
            pkgs.qt6.qtbase
            pkgs.qt6.qttools     # if you use Qt tools like uic/moc/rcc explicitly, usually not needed since qtbase includes them
            pkgs.freenect
            pkgs.freeglut
            pkgs.libGLU
          ];

          shellHook = ''
            echo "OpenCV dev shell ready. OpenCV_DIR: $OpenCV_DIR"
            echo "Qt6 dev shell ready. Qt6_DIR: $Qt6_DIR"
          '';
        };
      });
}
