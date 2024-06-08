## Part 2: Example for cluster usage of Datalad
*This part of hte code-along is largely based on the structure found in [this paper](https://www.biorxiv.org/content/10.1101/2021.10.12.464122v1) and has been adapted for this tutorial.*

In this part, we try to emulate the usage of datalad on a cluster on our own computer:
We take, still, the analysis  dataset, that we just created.
First, we copy the dataset to a new location, using datalad install:
*in analysis dataset*
```
datalad create-sibling-ria -s ria --new-store-ok --storage-sibling only ria+file://../ria
datalad push --to ria
cd ..
datalad clone analysis analysis_sink
```
After the processing of our data, we want the new dataset to hold the original data and the processed data. In our case, the processed data (the PDFs) are not that big, however, we can imagine situations, where each of the added files is multiple Gigabytes of data. We open a `ria-store`, a datalad repository that only holds the data. This is not tracked by git.

Now, if we look at the known siblings, we find that datalad is aware of
Now, we imagine that we want to process the rest of the data in parallel. We can parallelise this process "naively" aka we cen simply parallelise it as different jobs.
In this example, we will use a wrapper script that can basically be used as the basis to a SLURM script later on.
```
cd analysis
vim jobscript.sh
```
The heart of the job script will be the `datalad run` command from earlier.
The overall script looks somethign like this:
```
set -e -u -x

MYSOURCE=</absolute/path/to/the/dataset>
WORKDIR=/tmp/
MYSINK=</absolute/path/to/the/sink>
LOCK=~/dataset.lock

number=${1} # this can be replaced by something like ${SLURM_ARRAY_TASK_ID} on a SLURM managed cluster

datalad clone ${MYSOURCE} ${WORKDIR}/ds_${number}

cd ${WORKDIR}/ds_${number}

git remote add sink ${MYSINK}
git checkout -b calc_${number}

datalad install -r .
datalad siblings -d test-data enable -s uniS3

datalad run -i script.py -i test-data/data${number}.out -o plot${number}.pdf -m "add a second plot with a wrapper script" "python3 ./script.py test-data/data${number}.out plot${number}.pdf"

# publish
datalad push --to ria
flock ${LOCK} git push sink
```
Lets go through that line-by-line:
To make our lifes a litle easier, we first define some bash variables.
```
MYSOURCE=</absolute/path/to/the/dataset>
WORKDIR=/tmp/
MYSINK=</absolute/path/to/the/sink>
LOCK=~/dataset.lock

number = ${1}
```
They hold the most basic stuff that wewill need later in the execution of our code. `NYSOURCE` gives the place of the original dataset, `WORKDIR` the temporary directory, that we do our calculations in.
`number` is just a placeholder for some commandline argument.
Now the script actually starts.
first, we clone the original dataset to a temporary location and follow it:
```
datalad clone ${MYSOURCE} ${WORKDIR}/ds_${number}
cd ${WORKDIR}/ds_${number}
```
next, we add the sink as a git remote.
Now comes the part, because of which we do all of this.
with `git checkout -b calc_${number}`, we switch to a new git branch.
then, the command is run.
Before the end of the script, push the data to the ria store and make the new branch known to the sink-dataset. Since git does not like it if the push multiple commits at the exat same time, we use `flock` to make sure we are not interfering another push.
In priciple, if the temporary directory is not wiped automatically, we also need to dake care of cleaning up behind ourselves. This would be done with
```
datalad drop *
cd ${WORKDIR}
rm -rf ${WORKDIR}/ds_${number}
```
Once we fought our way out of `vim`, we save the changes to the dataset:
```
datalad save -m "added jobscript"
```
Cool, we have added the jobscript to the dataset. Now, we also make the sink aware of this change:
```
cd ../analysis_sink
datalad update --how=merge
```
We change back to the original repository nad execute our script:
```bash
cd ../analysis
bash jobscript.sh 3
```
Okay, if this looks good, we can change again to our sink and check if we indeed have a new branch tracked by git
```bash
cd ../analysis_sink
git branch
```
To incorporate the change into our dataset, we have to to two things: first, we merge the new branch into the `master` branch and delete the branch after merging
```bash
git merge calc_3
git branch -d calc_3
```
we can check, if the new plot is in the sink with `ls`.
If we try to gretrieve the data with `datalad get plot3.pdf`, we see, that this is not possible yet.
This is because the git annex here is not aware yet, that we pushed the data to our ria store. To change that, we use
```bash
git annex fsck -f ria
```
and try to get the data again using
```bash
datalad get plot3.pdf
```
et voila, there it is.

Now, we can also execute our wrapper "in parallel" in our shell:
```bash
cd ../analysis
for i in {4..7}; do ((bash jobscript.sh $i) &) ; done
```
and collect the different branches with
```bash
git merge calc_4
git merge calc_5
git merge calc_6
git merge calc_7
```
Finally, if we want to not do this for each branch separately, we can use
```bash
flock ../dataset.lock git merge -m "Merge results from calcs" $(git branch -l | grep "calc" | tr -d ' ')
git annex fsck -f ria
flock ../dataset.lock git branch -d $(git branch -l | grep "calc" | tr -d ' ')
```
where the `flock` is only necessary, if our cluster might still be working on some stuff.
