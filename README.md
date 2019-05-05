## QIIME2 for P2IRC canola
The .py file in this git was written for running on a server. Here I've tweaked it for a local machine (read: mostly made it shorter).

## Step 1: Install and activate miniconda and qiime.

##### Linux (server)
````
cd $HOME
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
````

##### MacOSX
```
cd $HOME
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh
```

##### Update miniconda
`
conda update conda
`

#####  Install (or update) wget
`
conda install wget
`

#### Install qiime2 (2019.1 version used here)

##### Linux
``
wget https://data.qiime2.org/distro/core/qiime2-2019.1-py36-linux-conda.yml
conda env create -n qiime2-2019.1 --file qiime2-2019.1-py36-linux-conda.yml
``

Optional cleanup: 
`
rm qiime2-2019.1-py36-linux-conda.yml
`

##### MacOSX
`
wget https://data.qiime2.org/distro/core/qiime2-2019.1-py36-osx-conda.yml
`

`
conda env create -n qiime2-2019.1 --file qiime2-2019.1-py36-osx-conda.yml
`

If you receive errors during the installation process, such as gfortran errors, please ensure you are following the installation instructions that are compatible with your platform.

Other errors are often resolved by running:
`
conda env remove -n qiime2-2019.1
`
to remove the failed environments, then running:
`
conda clean -y --all
`
to clean the local conda installation, and finally re-running the installation instructions above.

Note: To remove all files in a directory without deleting the directory
`
rm -rf directory/*
`

## Step 2: Make a directory to put your raw sequences in.
```
mkdir canola
cd canola/
mkdir raw_data
```
Note: To check to see where the directory is:
`
pwd
`
Or to go back to your home directory:
`
cd $HOME
`

## Step 3: Download some example data [here](https://www.dropbox.com/sh/maxd8uv1x55t5om/AAD8g1nLK6e8vQtksHuWLwE1a?dl=0).
````````````````````
ORIG1CR1101NW01000c_R1.fastq.gz
ORIG1CR1101NW01000c_R2.fastq.gz
ORIG1CR1101NW02000c_R1.fastq.gz
ORIG1CR1101NW02000c_R2.fastq.gz
ORIG1CR1101NW03000b_R1.fastq.gz
ORIG1CR1101NW03000b_R2.fastq.gz
ORIG1CR1101NW04000b_R1.fastq.gz
ORIG1CR1101NW04000b_R2.fastq.gz
ORIG1CR1101NW05000b_R1.fastq.gz
ORIG1CR1101NW05000b_R2.fastq.gz
ORIG1CR1101NW06000a_R1.fastq.gz
ORIG1CR1101NW06000a_R2.fastq.gz
ORIG1CR1101NW07000a_R1.fastq.gz
ORIG1CR1101NW07000a_R2.fastq.gz
ORIG1CR1101NW08000b_R1.fastq.gz
ORIG1CR1101NW08000b_R2.fastq.gz
ORIG1CR1101NW09000b_R1.fastq.gz
ORIG1CR1101NW09000b_R2.fastq.gz
ORIG1CR1101NW10000b_R1.fastq.gz
ORIG1CR1101NW10000b_R2.fastq.gz
````````````````````

## Step 4: Remove primers using cutadapt

The following pipeline was derived from qiime2 tutorials [moving pictures](https://docs.qiime2.org/2019.1/tutorials/moving-pictures/) and [Atacama soils](https://docs.qiime2.org/2019.1/tutorials/atacama-soils/). The cutadapt step was taken from the MicrobiomeHelper [tutorial](https://github.com/LangilleLab/microbiome_helper/wiki/Amplicon-SOP-v2-(qiime2-2018.8)).

#### Run cutadapt to remove the primers (342F, 806R)

For this to work, you should have the latest version of cutadapt (version 2.1) installed. I found I couldn't install it in the qiime2 environment and had to install in my base environment. I run the cutadapt step outside of qiime2.

Note: if you mess up and want to stop a process from running, press ctrl and c to kill it.

First make this directory in canola. This is where you'll transfer the manifest.csv file to (more on that shortly).

`
mkdir primer_trimmed_fastqs
`

The 
`--jobs N 
`
refers to how many processors the command will tap into. The max will depend on your machine. My computer only has 4, so let's use that here. The command assumes the data are in a folder in your active directory called "raw_data".

`
conda install -c bioconda cutadapt
`

Use 
`
cutadapt --version
`
to check which version you've got installed. Note: You may have to uninstall the previous version if it's present (1.18). Repeat the following step until you get an error message and then try to re-install the latest version:

`
conda uninstall cutadapt
`

Now you're ready to run cutadapt to remove the primers from the raw sequence data.

```````````
parallel --link --jobs 4   'cutadapt \
    --pair-filter any \
    --no-indels \
    --discard-untrimmed \
    -g CTACGGGGGGCAGCAG \
    -G GGACTACCGGGGTATCT \
    --minimum-length 1 \
    -o primer_trimmed_fastqs/{1/} \
    -p primer_trimmed_fastqs/{2/} \
    {1} {2} \
    > primer_trimmed_fastqs/{1/}_cutadapt_log.txt'   ::: raw_data/*_R1*.fastq.gz ::: raw_data/*_R2*.fastq.gz
```````````

It's good to check that cutadapt ran correctly. Each sample's logfile created above can be parsed to put the counts of passing reads into a single table (cutadapt_log.txt by default). If there were only a few reads passing through, that tells you there has been a problem with the cutadapt step (most frequently it's using the wrong primers). 

We'll use a script created by Dr. Morgan [Langille](https://github.com/LangilleLab). You can view the script [here](https://github.com/LangilleLab/microbiome_helper/blob/master/parse_cutadapt_logs.py). You'll need to copy the script and paste it into a text editor in terminal. Here are the steps:

1. Use the vi editor to make a script called parse_cutadapt_logs.py
    `
    vi parse_cutadapt_logs.py
    `.
2. Press `i` to edit and then paste the code you copied.
3. Press esc key.
4. Press shift and enter `wq` to save the script.
5. Let terminal know this is an executable file by typing 
    `
    chmod a+x parse_cutadapt_logs.py
    `.
6. Run it
    `
    ./parse_cutadapt_logs.py -i primer_trimmed_fastqs/*log.txt
    `
7. Lastly, remove the intermediate cutadapt logfiles
    `
    rm primer_trimmed_fastqs/*log.txt
    `

Or if the script didn't run on all files for some reason, move these files to another folder for a rainy day
`
mv -v primer_trimmed_fastqs/*.txt cutadapt_log_files/
`

## Step 5: Import the primer-trimmed data as a qiime2 artifact

#### Activate qiime2

##### Linux
`
conda activate qiime2-2019.1
`

Note: To deactivate qiime2 use
`
conda deactivate qiime2-2019.1
`

#### MacOSX
`
source activate qiime2-2019.1
`

Note: To deactivate qiime2 use
`
source deactivate qiime2-2019.1
`

Test if qiime successfully activated
`
qiime --help
`

To keep the directory clean you can put the artifact files in a new directory

`
mkdir reads_qza
`

For files without the Illumina naming convention (e.g., ORIG1CR1101NW01000c_R1.fastq.gz) use the code below. You'll need a manifest file, which I normally use R to partially create. Here is the R code:

1. Tell R the directory you'd like to read sequence file names in from. Here is an example path, but we'll set this to our actual working directory:

    `
    path <- "/Volumes/P2IRC13/Data/DNA_sequencing/Taxonomy_tables/qiime2_canola_2016_2017/raw_data_name_standardized"
    `

2. Create a dataframe of the file names:

    `
    metadata <- data.frame(list.files(path))
    `

3. Output the data frame as a file you can now adjust to be a manifest file in Excel. I know Excel is *super unsexy* but it still works...

    `
    write.csv(metadata, "/Volumes/P2IRC13/Data/DNA_sequencing/Taxonomy_tables/qiime2_canola_2016_2017/manifest_Mar2019.csv")
    `

4. Extract the relevant information out of the sequence file name. This Excel [command](https://www.extendoffice.com/documents/excel/1623-excel-extract-text-before-space.html) will come in handy (just replace the " " with "_"):

    `
    =LEFT(B2,(FIND("_",B2,1)-1))
    `

Here's an example manifest file. The $PWD means your present working directory (where you're running your qiime pipeline from):

`````
sample-id	absolute-filepath	direction
B1	$PWD/primer_trimmed_fastqs/B1_S193_L001_R1_001.fastq.gz	forward
B1	$PWD/primer_trimmed_fastqs/B1_S193_L001_R2_001.fastq.gz	reverse
B3	$PWD/primer_trimmed_fastqs/B3_S194_L001_R1_001.fastq.gz	forward
B3	$PWD/primer_trimmed_fastqs/B3_S194_L001_R2_001.fastq.gz	reverse
`````

Note: Make sure this file is in the correct directory.

#### Now you're **finally** ready to import the sequences into qiime2.

Use the `import` command with the corresponding parameters in qiime2:

````
qiime tools import --type SampleData[PairedEndSequencesWithQuality] \
                   --input-path manifest.csv \
                   --output-path reads_qza/reads_trimmed.qza \
                   --input-format PairedEndFastqManifestPhred33
````

For files with the Illumina naming convention (e.g., B1_S193_L001_R1_001.fastq.gz) use the code below (no need for a manifest file):

````
qiime tools import --type SampleData[PairedEndSequencesWithQuality] \
                   --input-path primer_trimmed_fastqs \
                   --output-path reads_qza/reads_trimmed.qza \
                   --input-format CasavaOneEightSingleLanePerSampleDirFmt
````

**IMPORTANT NOTE:** Run the following after each step to make sure there aren't any errors in the file before proceeding to the next step:

`
qiime tools validate reads_qza/reads_trimmed.qza
`

Check how many reads made it through each step using another Langille [script](https://github.com/LangilleLab/microbiome_helper/blob/master/qiime2_fastq_lengths.py). You'll make this script similar to how you made the last one.

1. Use the vi editor to make a script called qiime2_fastq_lengths.py
    `
    qiime2_fastq_lengths.py
    `.
2. Press `i` to edit and then paste the code you copied.
3. Press esc key.
4. Press shift and enter `wq` to save the script.
5. Let terminal know this is an executable file by typing 
    `
    chmod a+x qiime2_fastq_lengths.py
    `.
6. Make a directory to put the output of the script in.
    `
    mkdir read_counts
    `
6. Run it. Note that the `--proc n` refers to the number of processors to commit to this. I'll use 4 again.
    `
    ./qiime2_fastq_lengths.py reads_qza/*.qza --proc 60 -o read_counts/read_counts.tsv
    `

Now you can inspect this file for how many reads made it through each step.


## Step 6: Filter based on quality scores and deblur

Deblur uses sequence error profiles to associate erroneous sequence reads with the true biological sequence from which they are derived, resulting in high quality sequence variant data. This is applied in two steps. First, an initial quality filtering process based on quality scores is applied. This method is an implementation of the quality filtering approach described by Bokulich et al. (2013).

````
qiime quality-filter q-score \
 --i-demux reads_qza/reads_trimmed.qza \
 --o-filtered-sequences reads_qza/reads_trimmed_filt.qza \
 --o-filter-stats filt_stats.qza
````

Check to make sure there aren't any errors in the above file:

`
qiime tools validate reads_qza/reads_trimmed_filt.qza
`

Make a qiime2 visualization object to look at using qiime2 [view](https://view.qiime2.org/). You'll use this to set your `--p-trim-length` in the deblur step that follows.

`
qiime demux summarize --i-data reads_qza/reads_trimmed_filt.qza --o-visualization reads_trimmed_filt_summary.qzv
`

Next, the Deblur workflow is applied using the qiime deblur denoise-16S method. This method requires one parameter that is used in
quality filtering, `--p-trim-length n` which truncates the sequences at position `n`. In general, the Deblur developers recommend setting this value to a length where the median quality score begins to drop too low.

```````
qiime deblur denoise-16S \
  --i-demultiplexed-seqs reads_qza/reads_trimmed_filt.qza \
  --p-trim-length 200 \
  --o-representative-sequences reads_qza/rep-seqs-deblur.qza \
  --o-table table-deblur.qza \
  --p-sample-stats \
  --o-stats deblur-stats.qza
```````

The two commands used in this section generate QIIME 2 artifacts containing summary statistics. To view those summary statistics, you can visualize them using qiime metadata tabulate and qiime deblur visualize-stats, respectively:

```
qiime deblur visualize-stats \
  --i-deblur-stats deblur-stats.qza \
  --o-visualization deblur-stats.qzv
```

Rename the files to match commands later in the qiime2 tutorials cited above

``
mv rep-seqs-deblur.qza rep-seqs.qza
mv table-deblur.qza table.qza
``

After the quality filtering step completes, you’ll want to explore the resulting data. You can do this using the following two commands, which will create visual summaries of the data. The feature-table summarize command will give you information on how many sequences are associated with each sample and with each feature, histograms of those distributions, and some related summary statistics.

The `feature-table tabulate-seqs` command will provide a mapping of feature IDs to sequences, and provide links to easily BLAST each sequence against the NCBI nt database. The latter visualization will be very useful later in the tutorial, when you want to learn more about specific features that are important in the data set.

Note: the metadata file may need to be saved as a tab-delimited format (metadata.txt). I ran into an error when using a comma-separated format. I saved the file as tab-delimited and that solved the problem.

Here's an example metadata file:

``````````
#SampleID	Treatment
#q2:types	categorical
# B1	control
# B3	control
# B4	control
# H4C4-1	treatment
# H4C4-2	treatment
# H4C4-3	treatment
# H4C4-4	treatment
# H4C4-5	treatment
``````````

This step is **optional** (requires metadata file):

````
qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization table.qzv \
  --m-sample-metadata-file metadata.tsv
````

Use this step to output a visualization to check how many samples made it through (look at on qiime 2 view):

```
qiime feature-table tabulate-seqs \
  --i-data reads_qza/rep-seqs.qza \
  --o-visualization rep-seqs.qzv
```

## Step 7: Make a taxonomic classifier and assign taxonomy

In the next sections we’ll begin to explore the taxonomic composition of the samples, and again relate that to sample metadata. The first step in this process is to assign taxonomy to the sequences in our FeatureData[Sequence] QIIME 2 artifact. We’ll do that using a pre-trained Naive Bayes classifier and the q2-feature-classifier plugin. We’ll apply this classifier to our sequences, and we can generate a visualization of the resulting mapping from sequence to taxonomy.

Note: Taxonomic classifiers perform best when they are trained based on your specific sample preparation and sequencing parameters, including the primers that were used for amplification and the length of your sequence reads. Therefore in general you should follow the instructions in Training feature classifiers with q2-feature-classifier to train your own taxonomic classifiers. We provide some common classifiers on our data resources page, including Silva-based 16S classifiers, though in the future we may stop providing these in favor of having users train their own classifiers which will be most relevant to their sequence data.

`````
qiime feature-classifier classify-sklearn \
  --i-classifier SILVA_V3_V5_342F_806R_qiime2_2019_1_classifier.qza \
  --p-n-jobs 4 \
  --i-reads reads_qza/rep-seqs.qza \
  --o-classification taxonomy.qza
`````

Use the following code to inspect the taxonomy on qiime 2 view:

```
qiime metadata tabulate \
  --m-input-file taxonomy.qza \
  --o-visualization taxonomy.qzv
```

**OPTIONAL** (requires metadata file): we can view the taxonomic composition of our samples with interactive bar plots. Generate those plots with the following command and then open the visualization:

`````
qiime taxa barplot \
  --i-table table.qza \
  --i-taxonomy taxonomy.qza \
  --m-metadata-file metadata.txt \
  --o-visualization taxa-bar-plots.qzv
`````

Export the final abundance and taxonomy files in `BIOM format` for import into R.

`
qiime tools export --input-path table.qza --output-path deblur_output_exported
`

`
qiime tools export --input-path taxonomy.qza --output-path deblur_output_exported
`

If you want to add taxonomy to the biom files, you can do this or just use the exported version above for downstream analyses:

Use vi to change headers in taxonomy.tsv from:
  
  `
  #Feature ID    Taxon    Confidence
  `

To:
      
  `
  #OTUID    taxonomy    confidence
  `

Make sure the headers are tab separated (tsv).

Add metadata

  `````
  biom add-metadata --input-fp deblur_output_exported/feature-table.biom \
  				  --sample-metadata-fp metadata.txt \
  				  --output-fp deblur_output_exported/qiime2-canola.biom \
  				  --observation-metadata-fp deblur_output_exported/taxonomy.tsv \
  				  --sc-separated taxonomy_2
  `````

## Much rejoicing. If you've made it this far, you're done with the hell known as bioinformatics. Now get ready for the **f**un that is R!
