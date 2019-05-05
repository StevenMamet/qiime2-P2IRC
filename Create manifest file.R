rm(list = ls()) # Clean workspace

path <- "/Users/sdmamet/Desktop/PLSC898/canola/raw_data"          # Set the path to where your sequence files are stored
manifest <- data.frame(list.files(path), stringsAsFactors = F)    # Create a dataframe of the file locations
sample_id <- strsplit(manifest$list.files.path., "[_]")[[1]][1]   # Extract the sample names
absolute_filepath <- paste("$PWD/primer_trimmed_fastqs/", 
                           manifest$list.files.path., sep = "")   # Make the file paths
direction <- rep(c("forward","reverse"), 10)                      # Make the read directions
manifest1 <- cbind.data.frame(sample_id, 
                              absolute_filepath, 
                              direction)                          # Make a new data frame including the required columns
names(manifest1) <- c("sample-id", 
                      "absolute-filepath", 
                      "direction")                                # Rename the columns
