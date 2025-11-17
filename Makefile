# --- Configuration Variables ---

# The name of the plugin source directory
PLUGIN_DIR := unity_terrain_exporter

# Extract the version directly from metadata.txt
# (Search for the line 'version=', then cut the 2nd part using '=' as delimiter)
VERSION := $(shell grep "version=" $(PLUGIN_DIR)/metadata.txt | cut -d '=' -f 2)

# The name of the output .zip file (ex: unity_terrain_exporter_v0.1.0.zip)
ZIP_FILE := $(PLUGIN_DIR)_v$(VERSION).zip

# --- Rules (Targets) ---

# Make 'all' and 'clean' targets "phony"
# This tells 'make' that they are commands, not files
.PHONY: all zip clean

# 'make' or 'make all' will execute the 'zip' rule by default
all: zip

# The main rule to create the .zip
zip:
	@echo "--- 📦 Creating plugin package (v$(VERSION)) ---"
	
	# Remove an old .zip file, if it exists, to avoid confusion
	@rm -f $(ZIP_FILE)
	
	# The main compression command
	# -r = recursive
	# -x = exclude files (we don't want to include __pycache__ or .pyc)
	@zip -r $(ZIP_FILE) $(PLUGIN_DIR) -x "*/__pycache__/*" "*.pyc"
	
	@echo "✅ Success! Package created: $(ZIP_FILE)"

# A rule to clean the generated files
clean:
	@echo "--- 🧹 Cleaning build files ---"
	@rm -f $(ZIP_FILE)
	@echo "Zip files removed."