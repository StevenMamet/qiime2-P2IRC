## QIIME2 for P2IRC canola
The .py file in this git was written for running on a server. Here I've tweaked it for a local machine (read: mostly made it shorter).

## Step 1: Install miniconda and qiime.

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
`
wget https://data.qiime2.org/distro/core/qiime2-2019.1-py36-linux-conda.yml
`

`
conda env create -n qiime2-2019.1 --file qiime2-2019.1-py36-linux-conda.yml
`

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

## Step 3: Download some example data [here](https://www.dropbox.com/sh/maxd8uv1x55t5om/AAD8g1nLK6e8vQtksHuWLwE1a?dl=0) or from the home directory above.
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

For this to work, you should have the latest version of cutadapt (version 2.1 or greater) installed. I found I couldn't install it in the qiime2 environment and had to install in my base environment. I run the cutadapt step outside of qiime2.

Parallel is required to run cutadapt as it's coded below. If you don't have parallel, you'll need to install it.

`ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null 2> /dev/null`
`brew install parallel`

Use 
`
cutadapt --version
`
to check which version you've got installed. 

To install cutadapt, use the following command:

`
conda install -c bioconda cutadapt
`

Note: You may have to uninstall the previous version if it's present (1.18). To uninstall, repeat the following step until you get an error message and then try to re-install the latest version (as above):

`
conda uninstall cutadapt
`

First make this directory in canola. This is where you'll transfer the manifest.csv file to (more on that shortly).

`
mkdir primer_trimmed_fastqs
`
Now you're ready to run cutadapt to remove the primers from the raw sequence data.

The 
`--jobs N 
`
refers to how many processors the command will tap into. The max will depend on your machine. My computer only has 4, so let's use that here. The command assumes the data are in a folder in your active directory called "raw_data".

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
4. Press `shift` + `:` and enter `wq` to save the script.
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

For files without the Illumina naming convention (e.g., ORIG1CR1101NW01000c_R1.fastq.gz) use the code below. You'll need a manifest file, which I normally use R to create. Here is the R code:

```````````````````````
# Set the path to where your sequence files are stored
path <- "~/Dropbox/CFREF Work/SteveM/2019_bootcamp/canola/raw_data"   

# Create a dataframe of the file locations
manifest <- data.frame(list.files(path), stringsAsFactors = F)

# Extract the sample names
sample_id <- sapply(strsplit(manifest$list.files.path., "_"), "[", 1)

# Make the file paths
absolute_filepath <- paste("$PWD/primer_trimmed_fastqs/", manifest$list.files.path., sep = "")       

# Make the read directions
direction <- rep(c("forward","reverse"), 10)           

# Make a new data frame including the required columns
manifest1 <- cbind.data.frame(sample_id, absolute_filepath, direction)

# Rename the columns
names(manifest1) <- c("sample-id", "absolute-filepath", "direction")

# Output the file
write.csv(manifest1, "~/Dropbox/CFREF Work/SteveM/2019_bootcamp/canola/manifest.csv", row.names = FALSE)

```````````````````````

Here's are the first five lines of an example manifest file. The $PWD means your present working directory (where you're running your qiime pipeline from):

`````
sample-id	absolute-filepath	direction
ORIG1CR1101NW01000c	$PWD/primer_trimmed_fastqs/ORIG1CR1101NW01000c_R1.fastq.gz	forward
ORIG1CR1101NW01000c	$PWD/primer_trimmed_fastqs/ORIG1CR1101NW01000c_R2.fastq.gz	reverse
ORIG1CR1101NW01000c	$PWD/primer_trimmed_fastqs/ORIG1CR1101NW02000c_R1.fastq.gz	forward
ORIG1CR1101NW01000c	$PWD/primer_trimmed_fastqs/ORIG1CR1101NW02000c_R2.fastq.gz	reverse
`````

Note: Make sure this file is in the correct directory.

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

## Step 6: Filter based on quality scores and deblur

Deblur uses sequence error profiles to associate erroneous sequence reads with the true biological sequence from which they are derived, resulting in high quality sequence variant data. This is applied in two steps. First, an initial quality filtering process based on quality scores is applied. This method is an implementation of the quality filtering approach described by Bokulich et al. (2013).

````
qiime quality-filter q-score \
 --i-demux reads_qza/reads_trimmed.qza \
 --o-filtered-sequences reads_qza/reads_trimmed_filt.qza \
 --o-filter-stats filt_stats.qza
````

Check to make sure there aren't any errors in the above file:

`qiime tools validate reads_qza/reads_trimmed_filt.qza`

Make a qiime2 visualization object to look at using qiime2 [view](https://view.qiime2.org/). You'll use this to set your `--p-trim-length` in the deblur step that follows.

```
qiime demux summarize \
  --i-data reads_qza/reads_trimmed_filt.qza \
  --o-visualization reads_trimmed_filt_summary.qzv
```

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
qiime metadata tabulate \
  --m-input-file filt_stats.qza \
  --o-visualization filt_stats.qzv
```

```
qiime deblur visualize-stats \
  --i-deblur-stats deblur-stats.qza \
  --o-visualization deblur-stats.qzv
```

Rename the files to match commands later in the qiime2 tutorials cited above

`mv rep-seqs-deblur.qza rep-seqs.qza`

`mv table-deblur.qza table.qza`

After the quality filtering step completes, you’ll want to explore the resulting data. You can do this using the following two commands, which will create visual summaries of the data. The feature-table summarize command will give you information on how many sequences are associated with each sample and with each feature, histograms of those distributions, and some related summary statistics.

The `feature-table tabulate-seqs` command will provide a mapping of feature IDs to sequences, and provide links to easily BLAST each sequence against the NCBI nt database. The latter visualization will be very useful later in the tutorial, when you want to learn more about specific features that are important in the data set.

Note: the metadata file may need to be saved as a tab-delimited format (metadata.txt). I ran into an error when using a comma-separated format. I saved the file as tab-delimited and that solved the problem.

You can validate your metadata beforehand using a Google Sheets add-on called [Keemei](https://keemei.qiime2.org/).

Here's an example metadata file:

````````````
#SampleID	Type	Year	Crop	RootSoil	Plot	FieldDuplicate	Week	DNAExt	PCRRun	SeqRep	Plate
#q2:types	categorical	categorical	categorical	categorical	categorical	categorical	numeric	categorical	categorical	categorical	categorical
ORIG1CR1101NW01000c	ORIG	1	C	R	1101	N	1	0	0	0	c
ORIG1CR1101NW02000c	ORIG	1	C	R	1101	N	2	0	0	0	c
ORIG1CR1101NW03000b	ORIG	1	C	R	1101	N	3	0	0	0	b
ORIG1CR1101NW04000b	ORIG	1	C	R	1101	N	4	0	0	0	b
ORIG1CR1101NW05000b	ORIG	1	C	R	1101	N	5	0	0	0	b
ORIG1CR1101NW06000a	ORIG	1	C	R	1101	N	6	0	0	0	a
ORIG1CR1101NW07000a	ORIG	1	C	R	1101	N	7	0	0	0	a
ORIG1CR1101NW08000b	ORIG	1	C	R	1101	N	8	0	0	0	b
ORIG1CR1101NW09000b	ORIG	1	C	R	1101	N	9	0	0	0	b
ORIG1CR1101NW10000b	ORIG	1	C	R	1101	N	10	0	0	0	b
````````````

Here's some R code, similar to making the _manifest_ file earlier to make the _metadata_ file above.

```````````````````````````````````
rm(list = ls()) # Clean workspace

# Set the path to where your sequence files are stored
path <- "~/Dropbox/CFREF Work/SteveM/2019_bootcamp/canola/raw_data"   

# Create a dataframe of the file locations
metadata <- data.frame(list.files(path), stringsAsFactors = F)

# Extract the sample names
sample_id <- sapply(strsplit(metadata$list.files.path., "_"), "[", 1)

# The file name contains the sample information
Type <- substr(sample_id, 1, 4)
Year <- substr(sample_id, 5, 5)
Crop <- substr(sample_id, 6, 6)
RootSoil <- substr(sample_id, 7, 7)
Plot <- substr(sample_id, 8, 11)
FieldDuplicate <- substr(sample_id, 12, 12)
Week <- substr(sample_id, 14, 15)
DNAExt <- substr(sample_id, 16, 16)
PCRRun <- substr(sample_id, 17, 17)
SeqRep <- substr(sample_id, 18, 18)
Plate <- substr(sample_id, 19, 19)

# Create the metadata data frame
metadata1 <- cbind.data.frame(sample_id, Type, Year, Crop, RootSoil, Plot, FieldDuplicate, Week, DNAExt, PCRRun, SeqRep, Plate)

# Rows are duplicated because we have information at the read-level (R1, R2). Change this to sample-level.
metadata1 <- metadata1[!duplicated(metadata1), ]

# Output the file
write.csv(metadata1, "~/Dropbox/CFREF Work/SteveM/2019_bootcamp/canola/metadata.csv", row.names = FALSE)
```````````````````````````````````

I added the subcolumn headings in Excel and saved as tab-delimited format.

This step is **optional** (requires metadata file):

````
qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization table.qzv \
  --m-sample-metadata-file metadata.txt
````

Use this step to output a visualization to check how many samples made it through (look at on qiime 2 view):

```
qiime feature-table tabulate-seqs \
  --i-data reads_qza/rep-seqs.qza \
  --o-visualization rep-seqs.qzv
```

## Step 7: Make a taxonomic classifier and assign taxonomy

In the next sections we’ll begin to explore the taxonomic composition of the samples, and again relate that to sample metadata. The first step in this process is to assign taxonomy to the sequences in our FeatureData[Sequence] QIIME 2 artifact. We’ll do that using a pre-trained Naive Bayes classifier and the q2-feature-classifier plugin. We’ll apply this classifier to our sequences, and we can generate a visualization of the resulting mapping from sequence to taxonomy.

Note: Taxonomic classifiers perform best when they are trained based on your specific sample preparation and sequencing parameters, including the primers that were used for amplification and the length of your sequence reads. 

Here we'll train a classifier using our V3-V5 regions of interest.

The latest Silva reference dataset is available [here](https://www.arb-silva.de/fileadmin/silva_databases/qiime/Silva_132_release.zip). Download and extract it to use in the following step.

First, import the reference sequences and taxonomy into qiime2.

````
qiime tools import \
  --type 'FeatureData[Sequence]' \
  --input-path /Volumes/P2IRC13/Data/DNA_sequencing/Databases/Silva_132_release/rep_set/rep_set_16S_only/99/silva_132_99_16S.fna \
  --output-path 99_otus.qza
````

`````
qiime tools import \
  --type 'FeatureData[Taxonomy]' \
  --input-format HeaderlessTSVTaxonomyFormat \
  --input-path /Volumes/P2IRC13/Data/DNA_sequencing/Databases/Silva_132_release/taxonomy/16S_only/99/majority_taxonomy_all_levels.txt \
  --output-path ref_all_levels_taxonomy.qza
`````

Extract the reference reads.

`````
qiime feature-classifier extract-reads \
  --i-sequences 99_otus.qza \
  --p-f-primer CTACGGGGGGCAGCAG \
  --p-r-primer GGACTACCGGGGTATCT \
  --o-reads ref_seqs.qza
`````

Now you're ready to train the classifier.

````
qiime feature-classifier fit-classifier-naive-bayes \
  --i-reference-reads ref_seqs.qza \
  --i-reference-taxonomy ref_all_levels_taxonomy.qza \
  --o-classifier SILVA_V3_V5_342F_806R_qiime2_2019_1_classifier.qza
````

#### Use the classifier you've trained above to classify your representative sequences

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
