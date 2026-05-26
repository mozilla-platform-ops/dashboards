BASE_URL ?= http://localhost:3000
TOKEN_REF ?= op://RelOps/Grafana Yardstick Service Account Token/credential
CONTEXT ?= yardstick

export BASE_URL
export TOKEN_REF

# RelSRE folder UIDs to enumerate for `make discover-uids`. The on-disk
# slug mapping lives in scripts/backup.py (FOLDERS); keep them in sync.
FOLDER_UIDS := \
  edtgaia1z6waoe \
  efmrv608qkr28f bfmrv6ezxze9sa ffmrv6e11wge8e \
  cffmfl1sfr1moe afm3plxpfbhfkb cfm3q22tcfpq8a bfib9xp9idu68b \
  cedp4g145xuyod

.PHONY: help login backup diff check-proxy discover-uids

help:
	@echo "make login         one-time gcx login against the local IAP proxy (token from 1Password)"
	@echo "make backup        pull RelSRE dashboards + alert rules into dashboards/ and alerts/"
	@echo "make diff          back up into a temp dir and diff against the live tree"
	@echo "make discover-uids list current dashboard UIDs in each tracked folder (refresh FOLDERS in scripts/backup.py)"

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
	./scripts/backup.py

diff: check-proxy
	@tmp=$$(mktemp -d) && \
	  ln -s $(CURDIR)/scripts $$tmp/scripts && \
	  (cd $$tmp && ./scripts/backup.py) && \
	  diff -r dashboards/ $$tmp/dashboards/ ; \
	  diff -r alerts/ $$tmp/alerts/ ; true

discover-uids: check-proxy
	@token=$${GRAFANA_TOKEN:-$$(op read "$(TOKEN_REF)")}; \
	for f in $(FOLDER_UIDS); do \
	  title=$$(curl -sS -H "Authorization: Bearer $$token" "$(BASE_URL)/api/folders/$$f" | jq -r '.title'); \
	  echo "## $$title ($$f)"; \
	  curl -sS -H "Authorization: Bearer $$token" "$(BASE_URL)/api/search?folderUIDs=$$f&type=dash-db&limit=500" \
	    | jq -r '.[] | "  \(.uid)\t\(.title)"'; \
	done
