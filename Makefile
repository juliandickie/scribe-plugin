# Scribe plugin maintenance targets.
# Run `make help` to see what's available.

.PHONY: help validate publish icons clean release-notes orient

# Override on the command line, e.g. make publish VERSION=0.2.1
VERSION ?=

help: ## Show available targets and what they do
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

validate: ## Validate manifests parse and skill structure is intact
	@python3 -m json.tool .claude-plugin/plugin.json > /dev/null && echo "  plugin.json - valid JSON"
	@python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "  marketplace.json - valid JSON"
	@for skill in workspace auth-init auth-add auth-status push client-resolve; do \
		test -f skills/$$skill/SKILL.md && echo "  skills/$$skill/SKILL.md - present" || (echo "  MISSING - skills/$$skill/SKILL.md"; exit 1); \
	done
	@grep -q "name" .claude-plugin/plugin.json && echo "  plugin name field - present"
	@grep -q "mcpServers" .claude-plugin/plugin.json && echo "  mcpServers - declared"

publish: ## Bump version, commit, tag, push, cut GH release. Usage - make publish VERSION=0.2.1
	@if [ -z "$(VERSION)" ]; then \
		echo "ERROR - set VERSION, e.g. make publish VERSION=0.2.1"; \
		exit 1; \
	fi
	@if ! command -v jq >/dev/null; then echo "ERROR - jq required"; exit 1; fi
	@if ! command -v gh >/dev/null; then echo "ERROR - gh CLI required"; exit 1; fi
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR - working tree dirty. Commit or stash first."; \
		git status --short; \
		exit 1; \
	fi
	@echo "Bumping version to $(VERSION) in plugin.json and marketplace.json..."
	@jq --arg v "$(VERSION)" '.version = $$v' .claude-plugin/plugin.json > .claude-plugin/plugin.json.tmp && \
		mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
	@jq --arg v "$(VERSION)" '.plugins[0].version = $$v' .claude-plugin/marketplace.json > .claude-plugin/marketplace.json.tmp && \
		mv .claude-plugin/marketplace.json.tmp .claude-plugin/marketplace.json
	@$(MAKE) --no-print-directory validate
	@echo ""
	@echo "Committing..."
	@git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
	@git commit -m "Release v$(VERSION)"
	@echo "Tagging v$(VERSION)..."
	@git tag -a v$(VERSION) -m "Scribe v$(VERSION)"
	@echo "Pushing main and tag..."
	@git push origin main v$(VERSION)
	@echo ""
	@echo "Creating GitHub release with auto-generated notes..."
	@gh release create v$(VERSION) --title "Scribe v$(VERSION)" --generate-notes
	@echo ""
	@echo "DONE - https://github.com/juliandickie/scribe-plugin/releases/tag/v$(VERSION)"

icons: ## Regenerate icon variants (512/256/128/64/32) from docs/images/icon-1024.png
	@if ! command -v magick >/dev/null; then echo "ERROR - ImageMagick required"; exit 1; fi
	@if [ ! -f docs/images/icon-1024.png ]; then \
		echo "ERROR - docs/images/icon-1024.png not found. Generate the master icon first."; \
		exit 1; \
	fi
	@for size in 512 256 128 64 32; do \
		echo "  Generating icon-$$size.png..."; \
		magick docs/images/icon-1024.png -resize $${size}x$${size} -strip docs/images/icon-$${size}.png; \
	done
	@cp docs/images/icon-256.png docs/images/icon.png
	@echo "  Default icon.png set to 256 variant"
	@echo "DONE - regenerated 6 icon files"

release-notes: ## Print recent commits since the last tag (helps draft notes)
	@LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null) && \
		echo "Commits since $$LAST_TAG -" && \
		git log $$LAST_TAG..HEAD --oneline

orient: ## One-shot snapshot for new sessions - state, recent work, releases, version match, open issues
	@echo "=== Validation ==="
	@$(MAKE) --no-print-directory validate
	@echo ""
	@echo "=== Recent local commits ==="
	@git log --oneline -10
	@echo ""
	@echo "=== Published GitHub releases (latest 5) ==="
	@gh release list --repo juliandickie/scribe-plugin --limit 5 2>/dev/null || echo "  (gh CLI unavailable or not authenticated)"
	@echo ""
	@echo "=== Local manifest versions vs latest tag ==="
	@echo "  plugin.json:      $$(jq -r .version .claude-plugin/plugin.json 2>/dev/null || echo '?')"
	@echo "  marketplace.json: $$(jq -r '.plugins[0].version' .claude-plugin/marketplace.json 2>/dev/null || echo '?')"
	@echo "  latest git tag:   $$(git describe --tags --abbrev=0 2>/dev/null || echo 'no tags')"
	@echo ""
	@echo "=== Open issues on this repo ==="
	@gh issue list --repo juliandickie/scribe-plugin 2>/dev/null || echo "  (gh CLI unavailable)"
	@echo ""
	@echo "=== Open upstream design discussion (#771) ==="
	@gh issue view 771 --repo taylorwilsdon/google_workspace_mcp --json title,state --jq '"  " + .state + " - " + .title' 2>/dev/null || echo "  (unable to fetch upstream issue 771)"

clean: ## Remove generated artifacts (no-op for now)
	@echo "Nothing to clean"
