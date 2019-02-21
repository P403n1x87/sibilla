SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = sibilla
SOURCEDIR     = source/
BUILDDIR      = .

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
