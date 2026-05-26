BASE_URL ?= http://localhost:3000
TOKEN_REF ?= op://RelOps/Grafana Yardstick Service Account Token/credential
CONTEXT ?= yardstick

export BASE_URL
export TOKEN_REF

# RelSRE folder UIDs we mirror. Update this list when folders are added or
# removed in Yardstick. `make discover-uids` prints the live state.
FOLDER_UIDS := \
  edtgaia1z6waoe \
  efmrv608qkr28f bfmrv6ezxze9sa ffmrv6e11wge8e \
  cffmfl1sfr1moe afm3plxpfbhfkb cfm3q22tcfpq8a bfib9xp9idu68b \
  cedp4g145xuyod

# Dashboard UIDs inside the folders above. Refresh with `make discover-uids`
# when a dashboard is added or deleted.
DASHBOARD_UIDS := \
  yONsE5vZz _N4y0LpWk beleuqjq6k0zkb xqkIk8HZz NSKyosMZz wIJoZ4HWk ieg6Sho5 \
  azure-pickup-wait-timeline-v1 gcp-pickup-wait-timeline-v1 \
  linux-all-metrics-v1 linux-all-status-v1 linux-pickup-wait-timeline-v1 \
  mac-builders-metrics-v1 mac-builders-status-v1 \
  mac-signers-metrics-v1 mac-signers-status-v1 \
  mac-testers-metrics-v1 mac-testers-status-v1 \
  mac-pickup-wait-timeline-v1 \
  windows-all-metrics-v1 windows-all-resource-v3 windows-thermal-24h-v1 \
  windows-pickup-wait-timeline-v1 \
  jg4pplj workers-fxci-dev

empty :=
space := $(empty) $(empty)
comma := ,

FOLDER_CSV := $(subst $(space),$(comma),$(strip $(FOLDER_UIDS)))
DASHBOARD_CSV := $(subst $(space),$(comma),$(strip $(DASHBOARD_UIDS)))

.PHONY: help login backup push validate diff check-proxy discover-uids

help:
	@echo "make login           one-time gcx login against the local IAP proxy (token from 1Password)"
	@echo "make backup          pull RelSRE dashboards/folders via gcx and alert rules via /api/v1/provisioning"
	@echo "make push            gcx resources push -p resources (dashboards/folders only)"
	@echo "make validate        gcx resources validate -p resources"
	@echo "make diff            pull into a temp dir and diff against resources/"
	@echo "make discover-uids   list current dashboard UIDs in each tracked folder (refresh the Makefile lists)"

check-proxy:
	@curl -sS -o /dev/null --max-time 5 $(BASE_URL)/api/health || { \
	  echo "Yardstick IAP proxy not reachable at $(BASE_URL)."; \
	  echo "Start it with: mzcld iap --host yardstick.mozilla.org --proxy --port 3000"; \
	  exit 1; \
	}

login: check-proxy
	@token=$${GRAFANA_TOKEN:-$$(op read "$(TOKEN_REF)")}; \
	gcx login $(CONTEXT) --server $(BASE_URL) --token "$$token" --yes
	gcx config use-context $(CONTEXT)
	gcx config check

backup: check-proxy
	gcx resources pull dashboards/$(DASHBOARD_CSV) folders/$(FOLDER_CSV) -p resources -o yaml
	./scripts/pull_alerts.py

push: check-proxy
	gcx resources push -p resources

validate: check-proxy
	gcx resources validate -p resources

diff: check-proxy
	@tmp=$$(mktemp -d) && \
	  gcx resources pull dashboards/$(DASHBOARD_CSV) folders/$(FOLDER_CSV) -p $$tmp/resources -o yaml >/dev/null && \
	  diff -r resources/ $$tmp/resources/ || true

discover-uids: check-proxy
	@token=$${GRAFANA_TOKEN:-$$(op read "$(TOKEN_REF)")}; \
	for f in $(FOLDER_UIDS); do \
	  title=$$(curl -sS -H "Authorization: Bearer $$token" "$(BASE_URL)/api/folders/$$f" | jq -r '.title'); \
	  echo "## $$title ($$f)"; \
	  curl -sS -H "Authorization: Bearer $$token" "$(BASE_URL)/api/search?folderUIDs=$$f&type=dash-db&limit=500" \
	    | jq -r '.[] | "  \(.uid)\t\(.title)"'; \
	done
