.PHONY: api-compile api-seed api-generate-key
.PHONY: api-bootstrap

api-compile:
	python3 -m compileall apps/api/app scripts/seed_master_admin.py

api-seed:
	python3 scripts/seed_master_admin.py

api-bootstrap:
	bash scripts/bootstrap_backend.sh

api-generate-key:
	python3 scripts/generate_fernet_key.py
