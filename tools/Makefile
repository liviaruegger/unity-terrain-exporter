# Makefile for development tools
# Provides convenient commands for generating and visualizing terrain files

.PHONY: help generate visualize visualize-3d pipeline clean-sample all clean

# Default target
help:
	@echo "Development Tools - Available Commands:"
	@echo ""
	@echo "  make pipeline [FILE=<input.tif>] [OUTPUT=<output.raw>] [OPTIONS=--3d-only|--images-only]"
	@echo "    🚀 Complete pipeline: Convert GeoTIFF to .raw AND visualize it"
	@echo "    If FILE not specified, uses samples/example.tif"
	@echo ""
	@echo "  make visualize-3d [FILE=<file.raw>] [WIDTH=...] [HEIGHT=...] [MIN=...] [MAX=...] [VAR=...]"
	@echo "    📺 Show interactive 3D visualization only"
	@echo "    If FILE not specified, uses samples/example.tif (converts automatically)"
	@echo ""
	@echo "  make visualize-images [FILE=<file.raw>] [WIDTH=...] [HEIGHT=...] [MIN=...] [MAX=...] [VAR=...]"
	@echo "    📸 Export 4 separate high-res images (300 DPI) only"
	@echo "    If FILE not specified, uses samples/example.tif (converts automatically)"
	@echo ""
	@echo "  make generate FILE=<input.tif> OUTPUT=<output.raw>"
	@echo "    Generate .raw file from GeoTIFF (without visualization)"
	@echo ""
	@echo "Examples:"
	@echo "  make pipeline                                    # Uses samples/example.tif"
	@echo "  make pipeline FILE=../samples/terrain.tif"
	@echo "  make pipeline OPTIONS=--3d-only                  # Only interactive 3D"
	@echo "  make pipeline OPTIONS=--images-only             # Only export images"
	@echo "  make visualize-3d                    # Uses example.tif, shows 3D only"
	@echo "  make visualize-images                # Uses example.tif, exports 4 images only"

# Generate .raw file from GeoTIFF
generate:
	@if [ -z "$(FILE)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "❌ Error: FILE and OUTPUT required"; \
		echo "Usage: make generate FILE=<input.tif> OUTPUT=<output.raw>"; \
		exit 1; \
	fi
	@echo "🔄 Generating .raw file..."
	@python3 generate_raw.py "$(FILE)" "$(OUTPUT)"

# Visualize interactive 3D only
visualize-3d:
	@if [ -z "$(FILE)" ]; then \
		echo "💡 No FILE specified, using default: samples/example.tif"; \
		python3 pipeline.py --3d-only; \
	else \
		if [ -z "$(WIDTH)" ] || [ -z "$(HEIGHT)" ] || [ -z "$(MIN)" ] || [ -z "$(MAX)" ] || [ -z "$(VAR)" ]; then \
			echo "❌ Error: When FILE is specified, WIDTH, HEIGHT, MIN, MAX, VAR are required"; \
			echo "Usage: make visualize-3d FILE=<file.raw> WIDTH=<w> HEIGHT=<h> MIN=<min> MAX=<max> VAR=<var>"; \
			echo "   Or: make visualize-3d  (uses example.tif)"; \
			exit 1; \
		fi; \
		echo "📺 Opening interactive 3D visualization..."; \
		python3 visualize_raw.py "$(FILE)" "$(WIDTH)" "$(HEIGHT)" "$(MIN)" "$(MAX)" "$(VAR)" --3d-only; \
	fi

# Export 4 separate high-res images only
visualize-images:
	@if [ -z "$(FILE)" ]; then \
		echo "💡 No FILE specified, using default: samples/example.tif"; \
		python3 pipeline.py --images-only; \
	else \
		if [ -z "$(WIDTH)" ] || [ -z "$(HEIGHT)" ] || [ -z "$(MIN)" ] || [ -z "$(MAX)" ] || [ -z "$(VAR)" ]; then \
			echo "❌ Error: When FILE is specified, WIDTH, HEIGHT, MIN, MAX, VAR are required"; \
			echo "Usage: make visualize-images FILE=<file.raw> WIDTH=<w> HEIGHT=<h> MIN=<min> MAX=<max> VAR=<var>"; \
			echo "   Or: make visualize-images  (uses example.tif)"; \
			exit 1; \
		fi; \
		echo "📸 Exporting 4 high-res images (300 DPI)..."; \
		python3 visualize_raw.py "$(FILE)" "$(WIDTH)" "$(HEIGHT)" "$(MIN)" "$(MAX)" "$(VAR)" --images-only; \
	fi


# Complete pipeline: convert + visualize
pipeline:
	@echo "🚀 Running complete pipeline..."
	@python3 pipeline.py $(if $(FILE),"$(FILE)",) $(if $(OUTPUT),"$(OUTPUT)",) $(if $(OPTIONS),$(OPTIONS),)

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -f *.raw *.png
	@echo "✅ Cleaned"

