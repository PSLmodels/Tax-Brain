# bash commands for installing your package
git fetch origin tags 2.5.0 && \
  git checkout -b v2.5.0 2.5.0 && \
  pip install --no-deps -e .

apt-get install texlive -y
