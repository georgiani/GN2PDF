# syntax=docker/dockerfile:1

FROM ubuntu:latest
WORKDIR /
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -yq wget curl unzip texlive-latex-extra ghostscript && curl -s https://api.github.com/repos/rrthomas/pdfjam/releases/latest | grep "browser_download_url" | cut -d : -f 2,3 | tr -d \" | wget -qi - && unzip pdfjam*.zip