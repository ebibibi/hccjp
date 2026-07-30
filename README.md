# HCCJP

This repository contains the website and legacy infrastructure examples for
[Hybrid Cloud Community Japan (HCCJP)](https://www.hccjp.org/).

## Static website

The current WordPress content is archived as a static site that can be hosted
on Cloudflare Pages at no infrastructure cost. The snapshot includes:

- 93 WordPress posts and 6 fixed pages
- locally archived images used by those pages
- Connpass event pages for HCCJP meetings 71 through 75
- preserved legacy URL paths, an event archive, sitemap, Atom feed, 404 page,
  and security headers

### Build

```bash
python3 -m pip install -r requirements.txt
python3 -m scripts.site_builder --source site --output public
```

To refresh the source snapshot from the live WordPress and Connpass pages:

```bash
python3 -m scripts.snapshot_sources --output site
```

To run the checks:

```bash
ruff format --check scripts tests
ruff check scripts tests
coverage run --branch --source=scripts.site_builder -m pytest -q tests
coverage report --fail-under=80
uvx --from bandit bandit -q -r scripts
```

### Deploy to Cloudflare Pages

```bash
npx wrangler pages deploy public --project-name hccjp-org-mirror
```

Cloudflare Pages serves the generated files only. WordPress, PHP, a database,
and a paid application host are not required.

## Legacy infrastructure examples

The older directories remain as historical examples for the HCCJP hybrid
cloud lab:

- `Terraform/`: Azure VM, networking, and web resources
- `VMConfigure/`: Ansible configuration
- `Certificate/`: Azure Stack certificate utilities
- `HybridNetwork/`: hybrid network setup
- `NewOrganization/`: Azure Stack organization setup
