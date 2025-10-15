# ERP-BERHAN Updates Only — Migration & Deploy Stabilizer

This bundle contains only the files you need to stabilize Alembic migrations and Render pre-deploy:

- `scripts/migrations/automerge_and_upgrade.py` — Pre-deploy: dedup duplicate revision IDs, write a merge revision if multiple heads exist, then `alembic upgrade head`.
- `tools/dedupe_alembic.py` — Lists duplicate `revision` IDs.
- `tools/check_templates.py` — Verifies that every `render_template()` has a matching file under `templates/`.
- `.github/workflows/alembic-one-head.yml` — CI guard to enforce a single head.

## How to apply
Unzip this at the **repo root**, commit, and ensure Render pre-deploy uses:
```bash
python -m scripts.migrations.automerge_and_upgrade
```

## What we saw in your zip
- Found versions dir: /mnt/data/erp84/ERP-BERHAN-main/migrations/versions
- Duplicate revision IDs detected: {
  "20251010_seed_test_users_dev": [
    "/mnt/data/erp84/ERP-BERHAN-main/migrations/versions/0000_20251010_seed_test_users_dev_  # keep your actual parent_placeholder.py",
    "/mnt/data/erp84/ERP-BERHAN-main/migrations/versions/20251010_seed_test_users_and_device_placeholder.py"
  ],
  "a1b2c3d4e5f7": [
    "/mnt/data/erp84/ERP-BERHAN-main/migrations/versions/0000_a1b2c3d4e5f7_  # keep your current value if different_placeholder.py",
    "/mnt/data/erp84/ERP-BERHAN-main/migrations/versions/a1b2c3d4e5f7_add_user_dashboards_table.py"
  ],
  "c3d4e5f6g7h": [
    "/mnt/data/erp84/ERP-BERHAN-main/migrations/versions/0000_c3d4e5f6g7h_  # keep whatever yours is now_placeholder.py",
    "/mnt/data/erp84/ERP-BERHAN-main/migrations/versions/c3d4e5f6g7h_add_sku_to_inventory_items.py"
  ]
}
- Computed heads (best-effort, static): ['000c349c7249', '20241007_0001', '20250830_fix_rls_policies', '20250913_add_fk_indexes', '20251003_fix_kpi_sales_mv', '20251010_merge_heads_auto', '20251010_mfa_fields', '20251012_widen_ver', '20251014_cleanup_single_head', '20251014_merge_heads_for_77', '20251014_merge_heads_stable', '20251014_merge_to_single_head', '20251015_merge_heads_final', '4879f87e41ba', '5f2f3e2cb2c1', '8d0e1f2g3h4i', 'a0e29d7d0f58', 'ae590e676162', 'appr_rev_20251013_202016', 'automerge_20251015164041', 'd1b125e62d70', 'erp_backbone_20251013_0930', 'i1j2k3l4m5n']
