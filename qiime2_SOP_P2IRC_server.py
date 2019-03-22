##############################################################################################################################
##############################################################################################################################

# Running the classification on barley (but there's also peas, beans, and wheat...oh my)

# To get access to these servers, you'll need to contact Greg Oster <oster@cs.usask.ca>

# Log on to oats (use your UofS nsid and pw)
# ssh sdm231@oats.usask.ca
# or
# ssh sdm231@peas.usask.ca
# or
# ssh sdm231@beans.usask.ca
# or
ssh sdm231@barley.usask.ca

## Note: I've obtained more space in the u1 directory:
# cd /
# cd u1/sdm231/canola



# ****************************
# Step 1: Create your working directory on the server, and make a directory to put your raw sequences in

mkdir canola
cd canola/
mkdir raw_data

# Some tmp files are gigantic. Make a new tmp directory in your working folder.
# This is where any log, temporary files will go
mkdir qiime2-tmp/
export TMPDIR="$PWD/qiime2-tmp/"

# Note: Run large processes through screen (here I've named it 'canola'), so connectivity issues don't stop the pipeline from running (e.g., avoid "broken pipe" issues)
screen -d -R canola
# To exit, ctrl + a followed by d (think "detach")
# If it's not responding, you can exit (ctrl + a followed by d) and type:
screen -X -S canola quit

# Note: To check to see where the directory is:
pwd
# Or to go back to your home directory:
cd $HOME



# ****************************
# Step 2: Move the files you need on to the server:

# Exit from the server and cd to the directory that contains files you want to transfer.
# Transfer a single file:
scp /Volumes/P2IRC13/Data/DNA_sequencing/Taxonomy_tables/qiime2_canola_2016_2017/SILVA_V3_V5_342F_806R_ALL_classifier.qza sdm231@barley:/home/sdm231/canola
# Transfer all files from a directory (the "-r" means recursive)
scp -r raw_data/* sdm231@oats:/home/sdm231/canola/raw_data

# Note: I wanted to process all P2IRC canola (2016/2017, root/soil) together, but had to get around the different naming conventions (e.g., Casava versus ManifestPhred (2016) - see importing steps below).
# So I had to rename the 2016 files using one method, the 2017 another, and then move all onto the server and process in one go
# Renaming 2016 files. This removes the first 27 characters. Remove the "-n" to make the changes permanent (-n means run as a simulation, can replace with a "-v" for verbose
# or to see the files as they're renamed)
rename -n 's/.{27}(.*)/$1/' *

# Two steps are needed to have the 2017 samples match the 2016 names.
# First, remove the "_001" from the end of each file:
for filename in *.fastq.gz; do mv "$filename" "./$(echo "$filename" | sed -e 's/_001//g')";  done
# Second, remove the "_SXX_L001_" from the middle of each file:
for filename in *.fastq.gz; do mv "$filename" "./$(echo "$filename" | sed -e 's/_S.*L001//g')";  done

# The files associated with ORIG2CR1202NW02000L was crashing the first import step.
# I removed them and their associated entries in the manifest and metadata files

# Note: Here's a command to run in terminal to export R1/R2 read counts to a file (assumes fastq.gz format), to make sure the read counts match between forward and reverse files:
parallel "echo {} && gunzip -c {} | wc -l | awk '{d=\$1; print d/4;}'" ::: *.gz > /Users/sdmamet/Desktop/SeqCount.txt
# I'll import the above file into Excel to check for mismatching sequences (see the SeqCount.xlsx file for an example)



# ****************************
# Step 3: Install miniconda and qiime

# If not already installed, you'll have to install miniconda and qiime on the server following the Linux instructions
# Installing miniconda while logged onto the server:
## Note: the installation steps should only have be completed once. The next time you are bioinformatic'ing, you can just run the activate step.
cd $HOME
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"

# Update miniconda and install (or update) wget
conda update conda
conda install wget

# Installing qiime
wget https://data.qiime2.org/distro/core/qiime2-2019.1-py36-linux-conda.yml
conda env create -n qiime2-2019.1 --file qiime2-2019.1-py36-linux-conda.yml
# OPTIONAL CLEANUP
rm qiime2-2019.1-py36-linux-conda.yml

# OSX
# wget https://data.qiime2.org/distro/core/qiime2-2019.1-py36-osx-conda.yml
# conda env create -n qiime2-2019.1 --file qiime2-2019.1-py36-osx-conda.yml


# If you receive errors during the installation process, such as gfortran errors,
# please ensure you are following the installation instructions that are compatible with your platform.
# Other errors are often resolved by running:
# conda env remove -n qiime2-2019.1
# to remove the failed environments, then running:
# conda clean -y --all
# to clean the local conda installation, and finally re-running the installation instructions above.

# Activate qiime
# Linux
conda activate qiime2-2019.1
# conda deactivate qiime2-2019.1
# OSX
# source activate qiime2-2019.1

# Test if qiime successfully activated
qiime --help

# Note: To remove all files in a directory without deleting the directory:
rm -rf directory/*



# ****************************
# Step 4: Remove primers using cutadapt

# The following pipeline was derived from qiime2 tutorials available online:
# https://docs.qiime2.org/2019.1/tutorials/moving-pictures/
# https://docs.qiime2.org/2019.1/tutorials/atacama-soils/
# The cutadapt step was taken from the MicrobiomeHelper tutorial:
# https://github.com/LangilleLab/microbiome_helper/wiki/Amplicon-SOP-v2-(qiime2-2018.8)

# Run cutadapt to remove the primers (342F, 806R)

# Note: if you mess up and want to stop a process from running, press ctrl and c to kill it

# First make this directory in canola. Remember to transfer the manifest.csv file here
mkdir primer_trimmed_fastqs

# There are 64 cores to tap into so the --jobs N step can be set to N < 64. The command assumes the data are in a folder in your active directory called "raw_data"
# Note: the "--jobs 50" parameter tells the computer to use 50 cores. This will work on the server, but should
# choose a lower number to match the number of cores available locally.
# For this to work, you should have the latest version of cutadapt (version 2.1) installed.
# I found I couldn't install it in the qiime2 environment and had to install in my base environment on the server:
conda install cutadapt
# You may have to uninstall the version installed on the server first (1.18). Repeat this step until you get an error message and then try to re-install the latest version.
conda uninstall cutadapt
# Find out which version you have, run:
cutadapt --version
# I then ran it outside of qiime2 (e.g., conda deactivate qiime2-2019.1)

# P2IRC primers
parallel --link --jobs 60   'cutadapt \
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

# Cutadapt 1.18 and the qiime2 version were resulting in errors later on:
# qiime tools import --type SampleData[PairedEndSequencesWithQuality] \
#                    --input-path raw_data \
#                    --output-path reads_qza/reads.qza \
#                    --input-format CasavaOneEightSingleLanePerSampleDirFmt
#
# qiime cutadapt trim-paired --i-demultiplexed-sequences reads_qza/reads.qza \
# 	--p-cores 60 \
# 	--p-adapter-f CTACGGGGGGCAGCAG \
# 	--p-adapter-r GGACTACCGGGGTATCT \
# 	--output-dir primer_trimmed_fastqs/
#

# Each sample's logfile created above can be parsed to put the counts of
# passing reads into a single table (cutadapt_log.txt by default).
# I had to rename the files to remove the first "_0" and replace it with ".0". The sample name was
# derived from the leading characters prior to the "_0". This may not apply to all analyses.

# The following python file was included in Microbiome Helper, but not in native qiime.
# I made this file in Terminal on my local machine and uploaded to oats
vi parse_cutadapt_logs.py
# Press "i" to edit
# Paste the code from here:
https://github.com/LangilleLab/microbiome_helper/blob/master/parse_cutadapt_logs.py
# Press esc key
# Press shift and :
# Enter "wq" to save file
# Let Linux know this is an executable file
chmod a+x parse_cutadapt_logs.py

# Run it:
./parse_cutadapt_logs.py -i primer_trimmed_fastqs/*log.txt

# Lastly, remove the intermediate cutadapt logfiles:
rm primer_trimmed_fastqs/*log.txt

# Or if the script didn't run on all files for some reason, move these files to another folder for a rainy day
mv -v primer_trimmed_fastqs/*.txt cutadapt_log_files/



# ****************************
# Step 5: Import the primer-trimmed data as a qiime2 artifact

# To keep the directory clean you can put the artifact files in a new directory
mkdir reads_qza

# For files without the Illumina naming convention (e.g., CHCK1CR1101NW05001a_R1.fastq.gz) use the code below.
# You'll need a manifest file, which I normally use R to partially create (see the followng R code):
# * Tell R the directory you'd like to read sequence file names in from:
# path <- "/Volumes/P2IRC13/Data/DNA_sequencing/Taxonomy_tables/qiime2_canola_2016_2017/raw_data_name_standardized"
# * Create a dataframe of the file names:
# metadata <- data.frame(list.files(path))
# * Output the data frame as a file you can now adjust to be a manifest file in Excel:
# write.csv(metadata, "/Volumes/P2IRC13/Data/DNA_sequencing/Tax	onomy_tables/qiime2_canola_2016_2017/manifest_Mar2019.csv")
# This Excel command will come in handy (just replace the " " with "_"): https://www.extendoffice.com/documents/excel/1623-excel-extract-text-before-space.html
# =LEFT(B2,(FIND("_",B2,1)-1))

# Example manifest file. The $PWD means your present working directory (where you're running your qiime pipeline from):
# sample-id	absolute-filepath	direction
# B1	$PWD/primer_trimmed_fastqs/B1_S193_L001_R1_001.fastq.gz	forward
# B1	$PWD/primer_trimmed_fastqs/B1_S193_L001_R2_001.fastq.gz	reverse
# B3	$PWD/primer_trimmed_fastqs/B3_S194_L001_R1_001.fastq.gz	forward
# B3	$PWD/primer_trimmed_fastqs/B3_S194_L001_R2_001.fastq.gz	reverse

qiime tools import --type SampleData[PairedEndSequencesWithQuality] \
                   --input-path manifest.csv \
                   --output-path reads_qza/reads_trimmed.qza \
                   --input-format PairedEndFastqManifestPhred33

# For files with the Illumina naming convention (e.g., B1_S193_L001_R1_001.fastq.gz) use the code below (no need for a manifest file):
qiime tools import --type SampleData[PairedEndSequencesWithQuality] \
                   --input-path primer_trimmed_fastqs \
                   --output-path reads_qza/reads_trimmed.qza \
                   --input-format CasavaOneEightSingleLanePerSampleDirFmt

# IMPORTANT NOTE: Run the following after each step to make sure there aren't any errors in the file before proceeding to the next step:
qiime tools validate reads_qza/reads_trimmed.qza

# Check how many reads made it through each step (need to make this file similar to the previous python file)
# Make the directory first
mkdir read_counts
# Run the python script you create from:
# https://github.com/LangilleLab/microbiome_helper/blob/master/qiime2_fastq_lengths.py

# Note: the "--proc 50" parameter tells the computer to use 50 cores. This will work on the server, but should
# choose a lower number to match the number of cores available locally.
chmod a+x qiime2_fastq_lengths.py
./qiime2_fastq_lengths.py reads_qza/*.qza --proc 60 -o read_counts/read_counts.tsv



# ****************************
# Step 6: Filter based on quality scores and deblur

# Deblur uses sequence error profiles to associate erroneous sequence reads with the true biological sequence
# from which they are derived, resulting in high quality sequence variant data. This is applied in two steps.
# First, an initial quality filtering process based on quality scores is applied. This method is an implementation
# of the quality filtering approach described by Bokulich et al. (2013).
qiime quality-filter q-score \
 --i-demux reads_qza/reads_trimmed.qza \
 --o-filtered-sequences reads_qza/reads_trimmed_filt.qza \
 --o-filter-stats filt_stats.qza

# Check to make sure there aren't any errors in the above file:
qiime tools validate reads_qza/reads_trimmed_filt.qza

# Make the visualization object and transfer to your local machine to look at using qiime2 view to set your --p-trim-length:
qiime demux summarize --i-data reads_qza/reads_trimmed_filt.qza --o-visualization reads_trimmed_filt_summary.qzv

# Next, the Deblur workflow is applied using the qiime deblur denoise-16S method. This method requires one parameter that is used in
# quality filtering, --p-trim-length n which truncates the sequences at position n. In general, the Deblur developers recommend setting
# this value to a length where the median quality score begins to drop too low.
qiime deblur denoise-16S \
  --i-demultiplexed-seqs reads_qza/reads_trimmed_filt.qza \
  --p-trim-length 200 \
  --o-representative-sequences reads_qza/rep-seqs-deblur.qza \
  --o-table table-deblur.qza \
  --p-sample-stats \
  --o-stats deblur-stats.qza

# The two commands used in this section generate QIIME 2 artifacts containing summary statistics. To view those summary statistics, you can
# visualize them using qiime metadata tabulate and qiime deblur visualize-stats, respectively:
qiime deblur visualize-stats \
  --i-deblur-stats deblur-stats.qza \
  --o-visualization deblur-stats.qzv

# Rename the files to match commands later in the qiime2 tutorial
mv rep-seqs-deblur.qza rep-seqs.qza
mv table-deblur.qza table.qza

# After the quality filtering step completes, you’ll want to explore the resulting data.
# You can do this using the following two commands, which will create visual summaries of the data.
# The feature-table summarize command will give you information on how many sequences are associated
# with each sample and with each feature, histograms of those distributions, and some related summary statistics.
# The feature-table tabulate-seqs command will provide a mapping of feature IDs to sequences, and provide links
# to easily BLAST each sequence against the NCBI nt database. The latter visualization will be very useful later
# in the tutorial, when you want to learn more about specific features that are important in the data set.
# Note: the metadata file may need to be saved as a tab-delimited format (metadata.txt). I ran into an error when using a comma-separated format.
# I saved the file as tab-delimited and that solved the problem.
# Example metadata file:

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

# This step is optional (requires metadata file):
qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization table.qzv \
  --m-sample-metadata-file metadata.tsv

# Use this step to output a visualization to check how many samples made it through (look at on qiime 2 view)
qiime feature-table tabulate-seqs \
  --i-data reads_qza/rep-seqs.qza \
  --o-visualization rep-seqs.qzv



# ****************************
# Step 7: Assign taxonomy

# In the next sections we’ll begin to explore the taxonomic composition of the samples, and again relate that to sample metadata.
# The first step in this process is to assign taxonomy to the sequences in our FeatureData[Sequence] QIIME 2 artifact. We’ll do that
# using a pre-trained Naive Bayes classifier and the q2-feature-classifier plugin. We’ll apply this classifier to our sequences, and we
# can generate a visualization of the resulting mapping from sequence to taxonomy.

# Note: Taxonomic classifiers perform best when they are trained based on your specific sample preparation and sequencing parameters, including the primers
# that were used for amplification and the length of your sequence reads. Therefore in general you should follow the instructions in Training feature classifiers
# with q2-feature-classifier to train your own taxonomic classifiers. We provide some common classifiers on our data resources page, including Silva-based 16S classifiers,
# though in the future we may stop providing these in favor of having users train their own classifiers which will be most relevant to their sequence data.
qiime feature-classifier classify-sklearn \
  --i-classifier SILVA_V3_V5_342F_806R_qiime2_2019_1_classifier.qza \
  --p-n-jobs 60 \
  --i-reads reads_qza/rep-seqs.qza \
  --o-classification taxonomy.qza

# Use to inspect the taxonomy on qiime 2 view
qiime metadata tabulate \
  --m-input-file taxonomy.qza \
  --o-visualization taxonomy.qzv

# OPTIONAL (requires metadata file): we can view the taxonomic composition of our samples with interactive bar plots.
# Generate those plots with the following command and then open the visualization.
qiime taxa barplot \
  --i-table table.qza \
  --i-taxonomy taxonomy.qza \
  --m-metadata-file metadata.txt \
  --o-visualization taxa-bar-plots.qzv



# ****************************
# Step 7: Assign taxonomy

# Exporting the final abundance and sequence files (BIOM format)
qiime tools export --input-path table.qza --output-path deblur_output_exported
qiime tools export --input-path taxonomy.qza --output-path deblur_output_exported

# If you want to add taxonomy to the biom files, you can do this or just use the exported version above for downstream analyses.
## Add taxonomy to biom files

# Use vi to change headers in taxonomy.tsv from:
#    Feature ID    Taxon    Confidence
# To:
#    #OTUID    taxonomy    confidence

# Make sure headers are tab separated

# Add metadata
biom add-metadata --input-fp deblur_output_exported/feature-table.biom \
				  --sample-metadata-fp metadata.txt \
				  --output-fp deblur_output_exported/lulu_bacteria.biom \
				  --observation-metadata-fp deblur_output_exported/taxonomy.tsv \
				  --sc-separated taxonomy_2


# Exit the server and transfer the file back to your local machine ("*" means transfer all files)
scp -r sdm231@barley:/home/sdm231/canola/* ~/Desktop/folder

# Much rejoicing. If you've made it this far, you're done with the hell known as bioinformatics.

##############################################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################

## Other tidbits

# To count the number of files in the directory
ls | wc -l

# To count the number of sequences in a fastq.gz file
gunzip -c CHCK2CS1208NC02001S_R1.fastq.gz | wc -l

##############################################################################################################################

# Generate a tree for phylogenetic diversity analyses

# QIIME supports several phylogenetic diversity metrics, including Faith’s Phylogenetic Diversity and weighted and
# unweighted UniFrac. In addition to counts of features per sample (i.e., the data in the FeatureTable[Frequency]
# QIIME 2 artifact), these metrics require a rooted phylogenetic tree relating the features to one another.
# This information will be stored in a Phylogeny[Rooted] QIIME 2 artifact. To generate a phylogenetic tree we will
# use align-to-tree-mafft-fasttree pipeline from the q2-phylogeny plugin.

# First, the pipeline uses the mafft program to perform a multiple sequence alignment of the sequences in our FeatureData[Sequence]
# to create a FeatureData[AlignedSequence] QIIME 2 artifact. Next, the pipeline masks (or filters) the alignment to remove positions
# that are highly variable. These positions are generally considered to add noise to a resulting phylogenetic tree. Following that,
# the pipeline applies FastTree to generate a phylogenetic tree from the masked alignment. The FastTree program creates an unrooted tree,
# so in the final step in this section midpoint rooting is applied to place the root of the tree at the midpoint of the longest tip-to-tip
# distance in the unrooted tree.
qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences reads_qza/rep-seqs.qza \
  --o-alignment reads_qza/aligned-rep-seqs.qza \
  --o-masked-alignment reads_qza/masked-aligned-rep-seqs.qza \
  --o-tree unrooted-tree.qza \
  --o-rooted-tree rooted-tree.qza

# Alpha and beta diversity analysis in the qiime tutorial were skipped - too reliant on rarefaction

##############################################################################################################################

# Merging qza files from two separate runs - IF NECESSARY
# This has to happen after deblur

# Here I'm filtering the original feature table to make room for the re-processed features (i.e., so there are no duplicates)
qiime feature-table filter-samples \
  --i-table orig_seqs/table.qza \
  --m-metadata-file Samples-to-keep.csv \
  --o-filtered-table merge/id-filtered-table.qza

# Also need to filter the sequences that map to the original feature table
qiime feature-table filter-seqs \
  --i-data orig_seqs/representative_sequences.qza \
  --i-table merge/id-filtered-table.qza \
  --o-filtered-data merge/orig-rep-seqs-filt.qza

# Now merge with the March 2019 re-runs
qiime feature-table merge-seqs \
  --i-data merge/orig-rep-seqs-filt.qza \
  --i-data reads_qza/rep-seqs.qza \
  --o-merged-data rep-seqs_merged.qza

# Now merge with the March 2019 re-runs
qiime feature-table merge \
  --i-tables merge/orig-rep-seqs-filt.qza \
  --i-tables table.qza \
  --o-merged-table table_merged.qza
