{ pkgs ? import <nixpkgs> {} }:

pkgs.buildGoModule rec {
  pname = "media-processor";
  version = "0.0.1";

  vendorHash = pkgs.lib.fakeHash;

  meta = {
    description = "Media processing application with FFMPEG, written in Go";
  };

  nativeBuildInputs = with pkgs; [
    makeWrapper
  ];

  postFixup = ''
    wrapProgram $out/bin/transcoder \
      --set PATH ${pkgs.lib.makeBinPath (with pkgs; [
        ffmpeg-full
      ])}
  '';
}

# pkgs.writeScriptBin "transcoder" ''
# for file in "$@"
# do
# 	base=$(${pkgs.coreutils-full}/bin/basename "$file")
# 	filename="''${base%.*}"
# 	bitrate="2000K"

#   ${pkgs.ffmpeg-full}/bin/ffmpeg -ss 60 -t 60 -i "$file" -vf cropdetect -f null -
# 	${pkgs.ffmpeg-full}/bin/ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i "$file" -c:v hevc_nvenc -c:a copy -c:s copy -b:v "$bitrate" -map 0 "processing/''${filename}-''${bitrate}.mkv" < /dev/null
#   mv "processing/''${filename}-''${bitrate}.mkv" "processed/''${filename}-''${bitrate}.mkv"
# done

# echo "Finished!"
# ''
