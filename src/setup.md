## Docker setup
If you  want to foo along in an encapsulated docker environment, feel free to use the following configuration:
```dockerfile
FROM fedora:40

WORKDIR /home/root
RUN dnf update -y
RUN dnf install -y wget datalad pip vim

ARG user=dataladuser
ARG group=dataladuser
ARG uid=1000
ARG gid=1000
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -m ${user} # <--- the '-m' create a user home directory

# Switch to user
USER ${uid}:${gid}

WORKDIR /home/dataladuser

RUN git config --global user.email "j_kuhl19@uni-muenster.de"
RUN git config --global user.name "Justus Kuhlmann"
RUN pip3 install numpy scipy matplotlib
~
```
Run this by copying this into a Dockerfile, besure to change the `git config` parameters then use
```
docker build -t datalad .
docker run -it datalad
```
to build and run the container.
