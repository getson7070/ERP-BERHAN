"""Blueprint registry for ERP routes.

This subpackage exposes the various Flask blueprints used by ERP modules.
Importing ``erp.routes`` does not automatically register any blueprints; the
application factory is responsible for registering them via their ``bp``
attributes.  Modules include CRM (``erp.routes.crm``), finance
(``erp.routes.finance``), sales (``erp.sales.routes``), and more.
"""
__all__ = []
