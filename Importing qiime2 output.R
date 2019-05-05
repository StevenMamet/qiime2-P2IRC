# Only do these steps once. 
install.packages("BiocManager")
BiocManager::install("ALDEx2", version = "3.8")
install.packages('devtools')
devtools::install_github('ggloor/CoDaSeq/CoDaSeq')
BiocManager::install('phyloseq')
BiocManager::install('DESeq2')
BiocManager::install('biomformat')
BiocManager::install('CoDaSeq')

# Once the above have been done once, only need to load the packages now in each new session.
library(biomformat) # New version of biom
library(ade4) # Required by phyloseq
library(phyloseq) # Used to manipulate phylo data
library(plyr)
library(dplyr)
library(tidyr)
library(gdata)
library(stringr)
library(data.table)

rm(list = ls())

## Read in qiime2 biom file
canola.biom <- read_biom("/Users/sdmamet/Dropbox/CFREF Work/SteveM/2019_bootcamp/canola/deblur_output_exported/qiime2-canola.biom")

# ****************************
## Process abundance information
abundance <- data.frame(as.matrix(biom_data(canola.biom)), stringsAsFactors = F)
can.asv <- abundance

# ****************************
## Process taxonomic information
taxonomy <- observation_metadata(canola.biom)
taxa2 <- cbind.data.frame(kingdom = taxonomy$taxonomy1, 
                            phylum = taxonomy$taxonomy2, 
                            class = taxonomy$taxonomy3, 
                            order = taxonomy$taxonomy4, 
                            family = taxonomy$taxonomy5, 
                            genus = taxonomy$taxonomy6, 
                            species = taxonomy$taxonomy7)

# Remove the superfluous characters in each name ("D_0__", "D_1__", etc.)
Kingdom <- gsub("D_0__", "", taxa2$kingdom)
Phylum <- gsub("D_1__", "", taxa2$phylum)
Class <- gsub("D_2__", "", taxa2$class)
Order <- gsub("D_3__", "", taxa2$order)
Family <- gsub("D_4__", "", taxa2$family)
Genus <- gsub("D_5__", "", taxa2$genus)
Species <- gsub("D_6__", "", taxa2$species)

# Combine each taxonomic level into a matrix
taxa3 <- as.matrix(cbind(kingdom = Kingdom, phylum = Phylum, class = Class, order = Order, family = Family, genus = Genus, species = Species))

## Process the taxonomy information
# The subset_taxa command will remove rows with the specified taxonomy, but also NAs. 
# So recode the NAs to "unclassified" here to avoid removing extra rows.
# https://github.com/joey711/phyloseq/issues/683
can.tax <- as.data.frame(taxa3)
can.tax <- apply(can.tax, 2, 
                     function(x) 
                       gsub("^$|^ $", "unclassified", x))
can.tax[can.tax == "__"] <- "unclassified"
can.tax <- as.matrix(can.tax)                                   # Convert to matrix
row.names(can.tax) <- row.names(abundance)

# ****************************
## Process sample information
can.sam <- sample_metadata(canola.biom)
abu.colSums <- data.frame(colSums(abundance))
can.sam <- cbind.data.frame(abu.colSums, can.sam)
names(can.sam)[1] <- "SeqCount"

# Check the col and row sums for taxa or samples that have no read counts
# Calculate the column sums
can.asv.colsums <- colSums(can.asv)
can.asv.rowsums <- rowSums(can.asv)
# Count the non-zero sum columns
length(can.asv.colsums[can.asv.colsums != 0]); print("of"); length(can.asv.colsums)       # All columns have something in them
length(can.asv.rowsums[can.asv.rowsums != 0]); print("of"); length(can.asv.rowsums)       # All rows have something in them

## Check that the row and column names match up
identical(rownames(can.asv),rownames(can.tax))
identical(names(can.asv),rownames(can.sam))

# *************
## Make phyloseq class. Double check to see if the taxonomy columns are capitilized or not. This will affect the coding below.
can_all.asv <- phyloseq(otu_table(can.asv, taxa_are_rows = TRUE), sample_data(can.sam), tax_table(can.tax))
can_all.asv <- subset_taxa(can_all.asv, kingdom != "Archaea")                       # Remove archaea
can_all.asv <- subset_taxa(can_all.asv, class != "Chloroplast")                     # Remove chloroplasts
can_all.asv <- subset_taxa(can_all.asv, order != "Chloroplast")                     # Remove chloroplasts
can_all.no_mito <- subset_taxa(can_all.asv, family != "Mitochondria")               # Remove mitochondrial contaminant
can_all.fischeri <- subset_taxa(can_all.no_mito, genus == "Aliivibrio" )            # Collect Aliivibrio internal standard
can_all.no_mito.no_fischeri <- subset_taxa(can_all.no_mito, genus != "Aliivibrio")  # Remove internal standard from data set

## Using internal standard to correct abundances
fischeri <- as.vector(sample_sums(can_all.fischeri))                                # Create vector of internal standard
wi <- 1e-10                                                                         # Weight of internal standard gDNA added to the samples
gi <- 4.49e-15                                                                      # Weight of genome of the internal standard
ci <- 8                                                                             # 16S copy number of the internal standard
adj <- wi/gi*ci
fischeri.1 <- adj/fischeri
fischeri.1[is.infinite(fischeri.1)] <- 0

asv.table <- as.matrix(can_all.no_mito.no_fischeri@otu_table)                       # Export asv abundance table as matrix
asv.table.norm <- as.data.frame(sweep(asv.table, 2, fischeri.1, `*`))               # This divides the abundance matrix by the vector to normalize the data
tax.table.norm <- as.matrix(can_all.no_mito.no_fischeri@tax_table)                  # This extracts the taxonomic information exlcuding mitochondria & aliivibrio

## Get rid of unnecessary duplicates
can_all.norm <- phyloseq(otu_table(asv.table.norm, taxa_are_rows = TRUE), 
                         sample_data(can.sam), tax_table(tax.table.norm))      # Recreating a phyloseq object
can_all.norm <- prune_samples(sample_sums(can_all.norm) != 0, can_all.norm)
can_all.norm <- prune_taxa(taxa_sums(can_all.norm) != 0, can_all.norm)

## ****************
## Side note: collapse to genera
can_all.genus <- tax_glom(can_all.norm, "genus")
can_all.genus.asv <- data.frame(can_all.genus@otu_table)
can_all.genus.tax <- as.matrix(can_all.genus@tax_table)
can_all.genus.sam <- data.frame(can_all.genus@sam_data)
