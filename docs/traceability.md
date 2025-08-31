# Lot and Serial Tracking

The inventory module now supports tracking of lots and serial numbers with potency records.

- **Lots** record batch quantities with optional expiry dates.
- **Serials** link individual items to a lot for fine-grained traceability.
- **Potency** measurements capture strength over time.

Use the `/api/recall-simulate` endpoint to generate recall reports for a given lot.
